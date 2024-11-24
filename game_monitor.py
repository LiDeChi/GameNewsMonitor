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
        self.current_site_index = 0
        self.completed_sites = set()
        self.is_interrupted = False
        self.search_engines = []
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)

    async def _init_search_engines(self):
        """初始化搜索引擎"""
        self.search_engines = [
            GoogleSearch(self.context),
            BingSearch(self.context),
            DirectSiteSearch(self.context)
        ]

    async def _init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        
        # 尝试不同的浏览器启动配置
        browser_configs = [
            # 配置1：使用代理
            {
                'proxy': {
                    'server': 'socks5://127.0.0.1:7890'
                }
            },
            # 配置2：不使用代理
            {},
            # 配置3：使用其他代理设置
            {
                'proxy': {
                    'server': 'http://127.0.0.1:8080'
                }
            }
        ]
        
        for config in browser_configs:
            try:
                self.browser = await playwright.firefox.launch(
                    headless=True,
                    firefox_user_prefs={
                        'general.useragent.override': UserAgent().random
                    },
                    **config
                )
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=UserAgent().random
                )
                await self._init_search_engines()
                return
            except Exception as e:
                logging.warning(f"Browser config failed: {str(e)}, trying next config...")
                if self.browser:
                    await self.browser.close()
                    
        raise Exception("All browser configurations failed")

    async def search_new_pages(self, site: str, time_range: str) -> List[Dict]:
        """使用多个搜索引擎尝试获取结果"""
        for engine in self.search_engines:
            try:
                results = await engine.search(site, time_range)
                if results:  # 如果获取到结果就返回
                    logging.info(f"Successfully got results using {engine.__class__.__name__}")
                    return results
            except Exception as e:
                logging.error(f"Error using {engine.__class__.__name__}: {str(e)}")
                continue
        
        return []  # 如果所有搜索引擎都失败，返回空列表

    def _signal_handler(self, signum, frame):
        """处理中断信号"""
        logging.info("Received interrupt signal. Saving progress...")
        self.is_interrupted = True
        
    def _load_sites(self) -> List[str]:
        """加载要监控的网站列表"""
        try:
            with open('sites.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logging.error("sites.txt not found")
            return []
            
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

    async def monitor_all_sites(self, batch_size: int = 2):
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
