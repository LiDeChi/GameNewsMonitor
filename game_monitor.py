import os
import time
from datetime import datetime
import random
import requests
import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging
from urllib.parse import quote

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
        self.ua = UserAgent()
        
    def _load_sites(self):
        """加载要监控的网站列表"""
        try:
            with open('sites.txt', 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logging.error("sites.txt not found")
            return []

    def _get_random_headers(self):
        """生成随机请求头"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def search_new_pages(self, site, time_range):
        """搜索指定网站在特定时间范围内的新页面"""
        try:
            # 构建搜索URL
            if time_range == '24h':
                tbs = 'qdr:d'  # 最近24小时
            elif time_range == '1w':
                tbs = 'qdr:w'  # 最近1周
            else:
                raise ValueError(f"Invalid time range: {time_range}")

            query = f'site:{site}'
            url = f'https://www.google.com/search?q={quote(query)}&tbs={tbs}&num=100'
            
            # 发送请求
            response = requests.get(
                url,
                headers=self._get_random_headers(),
                timeout=10
            )
            response.raise_for_status()

            # 解析结果
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # 查找搜索结果
            for div in soup.find_all('div', class_='g'):
                try:
                    title_elem = div.find('h3')
                    if not title_elem:
                        continue
                        
                    link_elem = div.find('a')
                    if not link_elem:
                        continue
                        
                    url = link_elem.get('href')
                    if not url or not url.startswith('http'):
                        continue

                    snippet_elem = div.find('div', class_='VwiC3b')
                    snippet = snippet_elem.text if snippet_elem else ''

                    results.append({
                        'title': title_elem.text,
                        'url': url,
                        'snippet': snippet,
                        'site': site,
                        'time_range': time_range,
                        'found_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                except Exception as e:
                    logging.warning(f"Error parsing result for {site}: {str(e)}")
                    continue

            # 随机延迟，避免请求过快
            time.sleep(random.uniform(2, 5))
            return results

        except Exception as e:
            logging.error(f"Error processing {site}: {str(e)}")
            return []

    def monitor_all_sites(self):
        """监控所有网站的新页面"""
        all_results = []
        
        for site in self.sites:
            logging.info(f"Monitoring site: {site}")
            
            # 搜索最近24小时的新页面
            results_24h = self.search_new_pages(site, '24h')
            if results_24h:
                all_results.extend(results_24h)
            
            # 搜索最近一周的新页面
            results_1w = self.search_new_pages(site, '1w')
            if results_1w:
                all_results.extend(results_1w)
            
            # 随机延迟，避免触发反爬
            time.sleep(random.uniform(5, 10))

        # 保存结果到 CSV 文件
        if all_results:
            df = pd.DataFrame(all_results)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'game_news_{timestamp}.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logging.info(f"Results saved to {filename}")
        else:
            logging.info("No new pages found")

def main():
    try:
        monitor = GameMonitor()
        monitor.monitor_all_sites()
    except Exception as e:
        logging.error(f"Main program error: {str(e)}")

if __name__ == "__main__":
    main()
