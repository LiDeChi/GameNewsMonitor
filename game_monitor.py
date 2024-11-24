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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_monitor.log'),
        logging.StreamHandler()
    ]
)

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
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        
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

    async def _init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.firefox.launch(
            headless=True,
            firefox_user_prefs={
                "general.useragent.override": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

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

    async def _extract_search_results(self, page: Page) -> List[Dict]:
        """提取搜索结果"""
        results = []
        await page.wait_for_selector('div.g', timeout=30000)
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
                
        return results

    async def search_new_pages(self, site: str, time_range: str) -> List[Dict]:
        """搜索指定网站在特定时间范围内的新页面"""
        try:
            page = await self.context.new_page()
            
            if time_range == '24h':
                tbs = 'qdr:d'
            elif time_range == '1w':
                tbs = 'qdr:w'
            else:
                raise ValueError(f"Invalid time range: {time_range}")

            url = f'https://www.google.com/search?q=site:{site}&tbs={tbs}&num=20'
            
            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(random.uniform(2, 5))
            
            results = await self._extract_search_results(page)
            
            for result in results:
                result.update({
                    'site': site,
                    'time_range': time_range,
                    'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            await page.close()
            return results

        except Exception as e:
            logging.error(f"Error processing {site}: {str(e)}")
            return []

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

async def main():
    try:
        monitor = GameMonitor()
        await monitor.monitor_all_sites(batch_size=2)
    except Exception as e:
        logging.error(f"Main program error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
