import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import jieba
import jieba.analyse
from collections import Counter
import logging
from datetime import datetime
import matplotlib as mpl
from matplotlib.font_manager import FontProperties

class ResultAnalyzer:
    def __init__(self, input_file: str):
        self.input_file = input_file
        self.output_dir = Path('analysis_results')
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Zen Hei', 'Microsoft YaHei', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 使用 agg 后端避免 GUI 相关问题
        mpl.use('Agg')

    def analyze(self):
        """分析结果并生成报告"""
        try:
            df = pd.read_csv(self.input_file)
            
            # 生成图表
            self._plot_site_distribution(df)
            self._plot_time_distribution(df)
            self._plot_keyword_distribution(df)
            
            # 生成文本报告
            self._generate_report(df)
            
            logging.info("分析完成！报告已保存到 analysis_results/analysis_report.md")
            
        except Exception as e:
            logging.error(f"分析过程出错: {str(e)}")
            raise

    def _plot_site_distribution(self, df):
        """绘制网站分布图"""
        plt.figure(figsize=(10, 6))
        site_counts = df['site'].value_counts()
        sns.barplot(x=site_counts.values, y=site_counts.index)
        plt.title('各网站新闻数量分布')
        plt.xlabel('新闻数量')
        plt.ylabel('网站')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'site_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_time_distribution(self, df):
        """绘制时间分布图"""
        plt.figure(figsize=(10, 6))
        df['found_date'] = pd.to_datetime(df['found_date'])
        df['hour'] = df['found_date'].dt.hour
        hour_counts = df['hour'].value_counts().sort_index()
        sns.barplot(x=hour_counts.index, y=hour_counts.values)
        plt.title('新闻发布时间分布')
        plt.xlabel('小时')
        plt.ylabel('新闻数量')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'time_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_keyword_distribution(self, df):
        """绘制关键词分布图"""
        plt.figure(figsize=(12, 6))
        
        # 合并标题和摘要进行分析
        text = ' '.join(df['title'].fillna('') + ' ' + df['snippet'].fillna(''))
        
        # 使用 jieba 进行分词和关键词提取
        keywords = jieba.analyse.extract_tags(text, topK=20, withWeight=True)
        
        # 绘制关键词词云图
        words, weights = zip(*keywords)
        plt.barh(range(len(words)), weights)
        plt.yticks(range(len(words)), words)
        plt.title('热门关键词分布')
        plt.xlabel('权重')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'keyword_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()

    def _generate_report(self, df):
        """生成分析报告"""
        # 转换时间列
        df['found_date'] = pd.to_datetime(df['found_date'])
        
        # 计算24小时内和一周内的新闻数量
        now = pd.Timestamp.now()
        news_24h = df[df['found_date'] > (now - pd.Timedelta(days=1))]
        news_7d = df[df['found_date'] > (now - pd.Timedelta(days=7))]
        
        # 基本统计
        total_news = len(df)
        site_stats = df['site'].value_counts()
        
        # 提取游戏名称（从标题中提取括号内的内容）
        def extract_game_names(text):
            import re
            games = re.findall(r'[《\(（](.*?)[》\)）]', str(text))
            return games
            
        all_games = []
        for title in news_24h['title']:  # 只统计24小时内的游戏
            games = extract_game_names(title)
            all_games.extend(games)
        
        game_counts = Counter(all_games)
        top_games = game_counts.most_common(10)
        
        # 提取关键词（只从24小时内的新闻提取）
        text = ' '.join(news_24h['title'].fillna('') + ' ' + news_24h['snippet'].fillna(''))
        keywords = jieba.analyse.extract_tags(text, topK=20, withWeight=True)
        
        # 生成 Markdown 报告
        report = f"""# 游戏新闻数据分析报告

## 基本统计
- 总条目数: {len(news_24h)}
- 网站数量: {len(news_24h['site'].unique())}
- 24小时内新闻: {len(news_24h)}
- 一周内新闻: {len(news_7d)}

## 热门游戏 (Top 10)
| 游戏名称 | 提及次数 |
|---------|----------|
{chr(10).join([f'| {game} | {count} |' for game, count in top_games])}

## 热门关键词 (Top 20)
| 关键词 | 出现次数 |
|--------|----------|
{chr(10).join([f'| {word} | {int(count * 100)} |' for word, count in keywords])}
"""
        
        # 保存报告
        with open(self.output_dir / 'analysis_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
            
        # 保存24小时内的数据到CSV
        news_24h.to_csv(self.output_dir / 'game_news.csv', index=False, encoding='utf-8')

def main():
    # 获取最新的结果文件
    result_files = list(Path('.').glob('game_news_*.csv'))
    if not result_files:
        logging.error("未找到结果文件！")
        return
    
    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
    logging.info(f"分析文件: {latest_file}")
    
    # 创建分析器并生成报告
    analyzer = ResultAnalyzer(latest_file)
    analyzer.analyze()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()
