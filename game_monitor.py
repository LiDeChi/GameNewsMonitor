import asyncio
import random
import time
from datetime import datetime
import pandas as pd
import logging
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Dict, Optional
import json
import signal
import sys
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_monitor.log'),
        logging.StreamHandler()
    ]
)

class SearchEngine:
    """搜索引擎基类"""
    def __init__(self, context=None):
        self.context = context
        self.ua = UserAgent()

    async def search(self, site: str, time_range: str) -> List[Dict]:
        raise NotImplementedError

class GoogleSearch(SearchEngine):
    """Google搜索实现"""
    async def search(self, site: str, time_range: str) -> List[Dict]:
        try:
            if not self.context:
                return []

            page = await self.context.new_page()
            tbs = 'qdr:d' if time_range == '24h' else 'qdr:w'
            url = f'https://www.google.com/search?q=site:{site}&tbs={tbs}&num=20'
            
            await page.goto(url, timeout=60000)
            await asyncio.sleep(random.uniform(5, 8))
            
            results = []
            search_results = await page.query_selector_all('div.g')
            
            for result in search_results:
                try:
                    title_elem = await result.query_selector('h3')
                    if not title_elem:
                        continue
                    title = await title_elem.inner_text()
                    
                    link_elem = await result.query_selector('a')
                    if not link_elem:
                        continue
                    url = await link_elem.get_attribute('href')
                    if not url or not url.startswith('http'):
                        continue
                        
                    snippet_elem = await result.query_selector('div.VwiC3b')
                    snippet = await snippet_elem.inner_text() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
                except Exception as e:
                    logging.warning(f"Error extracting result: {str(e)}")
                    continue
            
            await page.close()
            return results
        except Exception as e:
            logging.error(f"Google search error: {str(e)}")
            return []

class BingSearch(SearchEngine):
    """Bing搜索实现"""
    async def search(self, site: str, time_range: str) -> List[Dict]:
        try:
            if not self.context:
                return []

            page = await self.context.new_page()
            freshness = 'Day' if time_range == '24h' else 'Week'
            url = f'https://www.bing.com/search?q=site:{site}&filters=ex1:"ez5_{freshness}"'
            
            await page.goto(url, timeout=60000)
            await asyncio.sleep(random.uniform(5, 8))
            
            results = []
            search_results = await page.query_selector_all('li.b_algo')
            
            for result in search_results:
                try:
                    title_elem = await result.query_selector('h2')
                    if not title_elem:
                        continue
                    title = await title_elem.inner_text()
                    
                    link_elem = await result.query_selector('a')
                    if not link_elem:
                        continue
                    url = await link_elem.get_attribute('href')
                    if not url or not url.startswith('http'):
                        continue
                        
                    snippet_elem = await result.query_selector('div.b_caption p')
                    snippet = await snippet_elem.inner_text() if snippet_elem else ''
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
                except Exception as e:
                    logging.warning(f"Error extracting result: {str(e)}")
                    continue
            
            await page.close()
            return results
        except Exception as e:
            logging.error(f"Bing search error: {str(e)}")
            return []

class DirectSiteSearch(SearchEngine):
    """直接访问网站实现"""
    def __init__(self, context=None):
        super().__init__(context)
        self.site_patterns = {
            '3dmgame.com': {
                'url': 'https://www.3dmgame.com/news/',
                'list_selector': '.news_list li',
                'title_selector': 'a.bt',
                'link_selector': 'a.bt',
                'snippet_selector': '.miaoshu'
            },
            'gamersky.com': {
                'url': 'https://www.gamersky.com/news/',
                'list_selector': '.contentpaging .txt',
                'title_selector': 'a',
                'link_selector': 'a',
                'snippet_selector': '.con'
            }
            # 可以继续添加其他网站的模式
        }

    async def search(self, site: str, time_range: str) -> List[Dict]:
        try:
            if site not in self.site_patterns:
                return []

            pattern = self.site_patterns[site]
            headers = {'User-Agent': self.ua.random}
            response = requests.get(pattern['url'], headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for item in soup.select(pattern['list_selector'])[:20]:
                try:
                    title_elem = item.select_one(pattern['title_selector'])
                    if not title_elem:
                        continue
                        
                    link_elem = item.select_one(pattern['link_selector'])
                    if not link_elem:
                        continue
                        
                    snippet_elem = item.select_one(pattern['snippet_selector'])
                    
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
                except Exception as e:
                    logging.warning(f"Error extracting result from {site}: {str(e)}")
                    continue
            
            return results
        except Exception as e:
            logging.error(f"Direct site search error for {site}: {str(e)}")
            return []

class GameMonitor:
    def __init__(self):
        self.sites = self._load_sites()
        self.browser: Optional[Browser] = None
        self.context = None
        self.results_file = None
        self.progress_file = 'progress.json'
        self.history_file = 'url_history.json'
        self.current_site_index = 0
        self.completed_sites = set()
        self.processed_urls = self._load_url_history()
        self.is_interrupted = False
        self.force_quit = False
        self.search_engines = []
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_sites(self) -> List[str]:
        """加载要监控的网站列表"""
        try:
            with open('sites.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logging.error("sites.txt not found")
            return []
            
    def _load_url_history(self) -> set:
        """加载已处理的URL历史记录"""
        try:
            if Path(self.history_file).exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # 只保留最近7天的历史记录
                    current_time = datetime.now()
                    filtered_history = {
                        url: timestamp for url, timestamp in history.items()
                        if (current_time - datetime.fromisoformat(timestamp)).days <= 7
                    }
                    return set(filtered_history.keys())
            return set()
        except Exception as e:
            logging.warning(f"加载URL历史记录失败: {str(e)}")
            return set()

    def _save_url_history(self):
        """保存已处理的URL历史记录"""
        try:
            current_time = datetime.now().isoformat()
            history = {url: current_time for url in self.processed_urls}
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"保存URL历史记录失败: {str(e)}")

    def _is_new_content(self, url: str, publish_time: Optional[str] = None) -> bool:
        """判断是否为新内容"""
        # 如果URL已经处理过，则不是新内容
        if url in self.processed_urls:
            return False
            
        # 如果提供了发布时间，检查是否在24小时内
        if publish_time:
            try:
                pub_time = datetime.fromisoformat(publish_time)
                time_diff = datetime.now() - pub_time
                if time_diff.days > 1:  # 超过24小时
                    return False
            except Exception as e:
                logging.warning(f"解析发布时间失败: {str(e)}")
                
        return True

    async def _process_search_results(self, results: List[Dict], site: str) -> List[Dict]:
        """处理搜索结果，过滤已处理的内容"""
        new_results = []
        for result in results:
            url = result.get('url', '')
            publish_time = result.get('publish_time')  # 如果搜索引擎或直接访问能获取到发布时间
            
            if self._is_new_content(url, publish_time):
                result.update({
                    'site': site,
                    'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                new_results.append(result)
                self.processed_urls.add(url)
                
        return new_results

    async def search_new_pages(self, site: str, time_range: str) -> List[Dict]:
        """使用多个搜索引擎尝试获取结果"""
        all_results = []
        success = False
        
        for engine in self.search_engines:
            try:
                results = await engine.search(site, time_range)
                if results:
                    # 过滤并处理新内容
                    new_results = await self._process_search_results(results, site)
                    all_results.extend(new_results)
                    logging.info(f"从 {site} 使用 {engine.__class__.__name__} 获取到 {len(new_results)} 条新内容")
                    success = True
                    
                    # 如果这个引擎成功了，继续尝试其他引擎以获取更多结果
                    continue
                    
            except Exception as e:
                logging.error(f"使用 {engine.__class__.__name__} 搜索 {site} 失败: {str(e)}")
                continue
                
        if not success:
            logging.warning(f"所有搜索引擎都未能从 {site} 获取到结果")
            
        # 对结果进行去重和排序
        unique_results = self._deduplicate_results(all_results)
        sorted_results = self._sort_results_by_time(unique_results)
        
        return sorted_results
        
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """对结果进行去重"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
                
        return unique_results
        
    def _sort_results_by_time(self, results: List[Dict]) -> List[Dict]:
        """按发布时间排序结果"""
        def get_time(result):
            try:
                time_str = result.get('publish_time', '')
                if time_str:
                    return datetime.fromisoformat(time_str)
                return datetime.min
            except Exception:
                return datetime.min
                
        return sorted(results, key=get_time, reverse=True)
        
    async def _init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        
        # 浏览器配置选项
        browser_configs = [
            # 1. 使用 Chromium（无代理）
            {
                'launch_type': 'chromium',
                'proxy': None,
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process'
                ]
            },
            # 2. 使用 Chromium（系统代理）
            {
                'launch_type': 'chromium',
                'proxy': {'server': 'system'},
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            },
            # 3. 使用 Firefox（备选）
            {
                'launch_type': 'firefox',
                'proxy': None,
                'args': ['--no-sandbox']
            }
        ]
        
        # 尝试不同的配置
        last_error = None
        for config in browser_configs:
            try:
                launch_args = {
                    'headless': True,
                    'args': config['args']
                }
                
                if config['proxy']:
                    launch_args['proxy'] = config['proxy']
                
                if config['launch_type'] == 'chromium':
                    self.browser = await playwright.chromium.launch(**launch_args)
                else:
                    self.browser = await playwright.firefox.launch(**launch_args)
                    
                # 创建上下文并设置用户代理
                self.context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                
                # 测试连接
                page = await self.context.new_page()
                await page.goto('https://www.google.com', timeout=30000)
                await page.close()
                
                logging.info(f"成功使用配置: {config['launch_type']}")
                await self._init_search_engines()
                return
                
            except Exception as e:
                last_error = e
                logging.warning(f"配置 {config['launch_type']} 失败: {str(e)}")
                if self.browser:
                    await self.browser.close()
                    
        raise Exception(f"所有浏览器配置都失败。最后的错误: {str(last_error)}")

    async def _init_search_engines(self):
        """初始化搜索引擎"""
        self.search_engines = [
            DirectSiteSearch(self.context),  # 直接访问放在第一位
            GoogleSearch(self.context),
            BingSearch(self.context)
        ]

    async def process_site_batch(self, sites: List[str]) -> None:
        """处理一批网站"""
        for site in sites:
            if site in self.completed_sites or self.is_interrupted:
                continue
                
            logging.info(f"Monitoring site: {site}")
            try:
                results_24h = await self.search_new_pages(site, '24h')
                if results_24h:
                    self._save_results(results_24h)
                
                results_1w = await self.search_new_pages(site, '1w')
                if results_1w:
                    self._save_results(results_1w)
                
                self.completed_sites.add(site)
                self._save_progress()
                
                await asyncio.sleep(random.uniform(10, 20))
                
            except Exception as e:
                logging.error(f"Failed to process site {site}: {str(e)}")
                continue

    async def monitor_all_sites(self, batch_size=2):
        """监控所有网站"""
        try:
            # 加载之前的进度
            self._load_progress()
            
            # 初始化浏览器
            await self._init_browser()
            
            # 从上次的位置继续处理
            total_sites = len(self.sites)
            for i in range(self.current_site_index, total_sites, batch_size):
                if self.is_interrupted:
                    break
                    
                self.current_site_index = i
                batch = self.sites[i:i + batch_size]
                logging.info(f"Processing batch {i//batch_size + 1}/{(total_sites + batch_size - 1)//batch_size}")
                
                await self.process_site_batch(batch)
                
                if i + batch_size < total_sites and not self.is_interrupted:
                    wait_time = random.uniform(60, 120)
                    logging.info(f"Waiting {wait_time:.0f} seconds before next batch...")
                    await asyncio.sleep(wait_time)
                    
        finally:
            # 保存最终进度
            self._save_progress()
            
            # 关闭浏览器
            if self.browser:
                await self.browser.close()
                
            if self.is_interrupted:
                logging.info("Task interrupted. Progress saved. Run the script again to continue.")
            else:
                logging.info("All sites processed successfully!")
                
            # 完成后保存URL历史
            self._save_url_history()

    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        if self.is_interrupted:  # 如果已经按过一次 Ctrl+C
            logging.info("强制退出程序...")
            self._force_cleanup()
            os._exit(1)  # 强制退出
        else:
            logging.info("收到中断信号，正在保存进度...再次按 Ctrl+C 强制退出")
            self.is_interrupted = True

    def _force_cleanup(self):
        """强制清理资源"""
        try:
            # 保存进度
            self._save_progress()
            self._save_url_history()
            
            # 关闭浏览器
            if self.browser:
                try:
                    asyncio.get_event_loop().run_until_complete(self.browser.close())
                except RuntimeError:
                    # 如果事件循环已关闭，创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.browser.close())
                    loop.close()
            
            # 关闭所有打开的文件
            try:
                for handler in logging.getLogger().handlers:
                    handler.close()
            except:
                pass
                
        except Exception as e:
            logging.error(f"清理资源时出错: {str(e)}")
        finally:
            # 确保所有输出都已刷新
            sys.stdout.flush()
            sys.stderr.flush()

    def _load_progress(self) -> None:
        """加载进度"""
        try:
            if Path(self.progress_file).exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    self.current_site_index = progress.get('last_site_index', 0)
                    self.completed_sites = set(progress.get('completed_sites', []))
                    logging.info(f"Loaded progress: Starting from site {self.current_site_index}")
        except Exception as e:
            logging.error(f"Error loading progress: {str(e)}")
            
    def _save_progress(self) -> None:
        """保存进度"""
        try:
            progress = {
                'last_site_index': self.current_site_index,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'completed_sites': list(self.completed_sites)
            }
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=4)
            logging.info(f"Progress saved: Completed {len(self.completed_sites)} sites")
        except Exception as e:
            logging.error(f"Error saving progress: {str(e)}")

    def _save_results(self, results: List[Dict]) -> None:
        """保存结果到CSV文件"""
        if not results:
            return
            
        if self.results_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.results_file = f'game_news_{timestamp}.csv'
            
        if not Path(self.results_file).exists():
            df = pd.DataFrame(results)
            df.to_csv(self.results_file, index=False, encoding='utf-8-sig')
        else:
            df = pd.DataFrame(results)
            df.to_csv(self.results_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        
        logging.info(f"Results saved to {self.results_file}")

async def main():
    try:
        monitor = GameMonitor()
        await monitor.monitor_all_sites(batch_size=2)
    except Exception as e:
        logging.error(f"Main program error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
