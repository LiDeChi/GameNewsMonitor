import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
from collections import Counter
import re
import jieba
from pathlib import Path
import logging

# 配置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False     # 解决负号显示问题

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class GameNewsAnalyzer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.output_dir = Path('analysis_results')
        self.output_dir.mkdir(exist_ok=True)
        
    def basic_statistics(self):
        """基本统计信息"""
        stats = {
            '总条目数': len(self.df),
            '网站数量': self.df['site'].nunique(),
            '24小时内新闻': len(self.df[self.df['time_range'] == '24h']),
            '一周内新闻': len(self.df[self.df['time_range'] == '1w'])
        }
        
        # 保存统计结果
        with open(self.output_dir / 'basic_stats.txt', 'w', encoding='utf-8') as f:
            for key, value in stats.items():
                f.write(f"{key}: {value}\n")
        
        return stats
    
    def analyze_by_site(self):
        """按网站分析数据"""
        site_stats = self.df.groupby('site').agg({
            'title': 'count',
            'time_range': lambda x: (x == '24h').sum()
        }).rename(columns={
            'title': '总新闻数',
            'time_range': '24小时内新闻数'
        })
        
        site_stats['一周内新闻数'] = site_stats['总新闻数'] - site_stats['24小时内新闻数']
        
        # 保存结果
        site_stats.to_csv(self.output_dir / 'site_statistics.csv', encoding='utf-8-sig')
        
        # 绘制柱状图
        plt.figure(figsize=(15, 8))
        site_stats[['24小时内新闻数', '一周内新闻数']].plot(kind='bar', stacked=True)
        plt.title('各网站新闻数量分布')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'site_distribution.png')
        plt.close()
        
        return site_stats
    
    def extract_game_names(self):
        """提取游戏名称"""
        def extract_names(text):
            # 这里可以根据实际情况添加更多的游戏名称提取规则
            patterns = [
                r'《(.*?)》',  # 中文书名号
                r'"(.*?)"',    # 英文引号
                r'\u2018(.*?)\u2019',    # 中文引号
            ]
            
            names = []
            for pattern in patterns:
                names.extend(re.findall(pattern, text))
            return names
        
        # 合并标题和描述
        self.df['content'] = self.df['title'] + ' ' + self.df['snippet'].fillna('')
        
        # 提取游戏名称
        all_games = []
        for content in self.df['content']:
            all_games.extend(extract_names(str(content)))
        
        # 统计频率
        game_counts = Counter(all_games)
        
        # 保存结果
        game_df = pd.DataFrame.from_dict(game_counts, orient='index', columns=['提及次数'])
        game_df.index.name = '游戏名称'
        game_df.sort_values('提及次数', ascending=False).to_csv(
            self.output_dir / 'game_mentions.csv',
            encoding='utf-8-sig'
        )
        
        return game_df
    
    def analyze_keywords(self):
        """分析关键词"""
        # 合并所有文本
        text = ' '.join(self.df['title'].fillna('') + ' ' + self.df['snippet'].fillna(''))
        
        # 分词
        words = jieba.cut(text)
        word_counts = Counter(words)
        
        # 过滤停用词和无意义词
        stop_words = {'的', '了', '和', '是', '在', '有', '与', '为', '及', '或', '等', 'the', 'a', 'an', 'of', 'to', 'in', 'for'}
        filtered_counts = {word: count for word, count in word_counts.items() 
                         if word not in stop_words and len(word) > 1}
        
        # 保存结果
        keywords_df = pd.DataFrame.from_dict(filtered_counts, orient='index', columns=['出现次数'])
        keywords_df.index.name = '关键词'
        keywords_df.sort_values('出现次数', ascending=False).head(100).to_csv(
            self.output_dir / 'keywords.csv',
            encoding='utf-8-sig'
        )
        
        return keywords_df
    
    def generate_report(self):
        """生成分析报告"""
        # 运行所有分析
        stats = self.basic_statistics()
        site_stats = self.analyze_by_site()
        game_stats = self.extract_game_names()
        keyword_stats = self.analyze_keywords()
        
        # 生成报告
        report = [
            "# 游戏新闻数据分析报告",
            f"\n## 基本统计",
            f"- 总条目数: {stats['总条目数']}",
            f"- 网站数量: {stats['网站数量']}",
            f"- 24小时内新闻: {stats['24小时内新闻']}",
            f"- 一周内新闻: {stats['一周内新闻']}",
            
            "\n## 热门游戏 (Top 10)",
            game_stats.sort_values('提及次数', ascending=False).head(10).to_markdown(),
            
            "\n## 热门关键词 (Top 20)",
            keyword_stats.sort_values('出现次数', ascending=False).head(20).to_markdown(),
            
            "\n## 详细结果",
            "完整的分析结果已保存到 analysis_results 目录下：",
            "- basic_stats.txt: 基本统计信息",
            "- site_statistics.csv: 各网站统计数据",
            "- site_distribution.png: 网站新闻分布图",
            "- game_mentions.csv: 游戏提及统计",
            "- keywords.csv: 关键词统计"
        ]
        
        # 保存报告
        with open(self.output_dir / 'analysis_report.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        logging.info("分析完成！报告已保存到 analysis_results/analysis_report.md")

def main():
    # 获取最新的结果文件
    result_files = list(Path('.').glob('game_news_*.csv'))
    if not result_files:
        logging.error("未找到结果文件！")
        return
    
    latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
    logging.info(f"分析文件: {latest_file}")
    
    # 创建分析器并生成报告
    analyzer = GameNewsAnalyzer(latest_file)
    analyzer.generate_report()

if __name__ == "__main__":
    main()
