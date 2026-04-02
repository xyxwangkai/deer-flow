#!/usr/bin/env python3
"""
从 CSV 文件中提取 insight 和 legend 的元数据信息。

用于帮助模型根据用户需求（如"关注评测相关图表"、"关注某某模型"）
筛选出对应的 insight_sid 或 legend，传入 single_analysis.py 进行分析。

输出格式：
{
    "insights": [
        {"insight_sid": "xxx", "insight_name": "评测名称", "legends": ["曲线1", "曲线2"]}
    ],
    "legends": ["所有曲线名称列表"],
    "legend_to_insights": {"曲线名": ["insight_sid1", "insight_sid2"]}
}
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd


def extract_metadata(csv_path: str) -> Dict[str, Any]:
    """
    从 CSV 文件中提取元数据
    
    Args:
        csv_path: CSV 文件路径
        
    Returns:
        包含 insights、legends、legend_to_insights 的字典
    """
    df = pd.read_csv(csv_path)
    
    required_cols = ['insight_sid', 'legend']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"CSV 文件缺少必需列: {col}")
    
    insight_name_col = None
    for col in ['insight_name', 'chart_name', 'name']:
        if col in df.columns:
            insight_name_col = col
            break
    
    insights = []
    insight_data = df.groupby('insight_sid')
    
    for insight_sid, group in insight_data:
        legends = group['legend'].unique().tolist()
        
        if insight_name_col:
            insight_name = group[insight_name_col].iloc[0]
        else:
            first_legend = legends[0] if legends else ""
            if '】-【' in first_legend:
                insight_name = first_legend.split('】-【')[-1].rstrip('】')
            elif '-' in first_legend:
                insight_name = first_legend.split('-')[-1]
            else:
                insight_name = insight_sid
        
        insights.append({
            "insight_sid": insight_sid,
            "insight_name": insight_name,
            "legend_count": len(legends),
            "legends": legends
        })
    
    all_legends = df['legend'].unique().tolist()
    
    legend_to_insights: Dict[str, List[str]] = {}
    for legend in all_legends:
        insight_sids = df[df['legend'] == legend]['insight_sid'].unique().tolist()
        legend_to_insights[legend] = insight_sids
    
    return {
        "total_insights": len(insights),
        "total_legends": len(all_legends),
        "insights": insights,
        "legends": all_legends,
        "legend_to_insights": legend_to_insights
    }


def search_by_keyword(metadata: Dict[str, Any], keyword: str) -> Dict[str, Any]:
    """
    根据关键词搜索匹配的 insight 和 legend
    
    Args:
        metadata: extract_metadata 返回的元数据
        keyword: 搜索关键词
        
    Returns:
        匹配的 insight_sids 和 legends
    """
    keyword_lower = keyword.lower()
    
    matched_insights = []
    for insight in metadata['insights']:
        if keyword_lower in insight['insight_name'].lower():
            matched_insights.append(insight['insight_sid'])
        elif keyword_lower in insight['insight_sid'].lower():
            matched_insights.append(insight['insight_sid'])
    
    matched_legends = []
    for legend in metadata['legends']:
        if keyword_lower in legend.lower():
            matched_legends.append(legend)
    
    return {
        "keyword": keyword,
        "matched_insight_sids": list(set(matched_insights)),
        "matched_legends": matched_legends
    }


def main():
    parser = argparse.ArgumentParser(
        description='从 CSV 文件中提取 insight 和 legend 元数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取所有元数据
  python3 extract_metadata.py case.csv
  
  # 输出到 JSON 文件
  python3 extract_metadata.py case.csv -o metadata.json
  
  # 搜索包含关键词的 insight 和 legend
  python3 extract_metadata.py case.csv -s "评测"
  python3 extract_metadata.py case.csv -s "M12"
  
  # 只输出 insight 列表（简洁模式）
  python3 extract_metadata.py case.csv --insights-only
  
  # 只输出 legend 列表
  python3 extract_metadata.py case.csv --legends-only
"""
    )
    
    parser.add_argument('input', help='输入 CSV 文件路径')
    parser.add_argument('-o', '--output', help='输出 JSON 文件路径')
    parser.add_argument('-s', '--search', help='搜索关键词，返回匹配的 insight_sid 和 legend')
    parser.add_argument('--insights-only', action='store_true', help='只输出 insight 列表')
    parser.add_argument('--legends-only', action='store_true', help='只输出 legend 列表')
    parser.add_argument('-q', '--quiet', action='store_true', help='安静模式，只输出 JSON')
    
    args = parser.parse_args()
    
    csv_path = Path(args.input)
    if not csv_path.exists():
        print(f"错误: 文件不存在: {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        metadata = extract_metadata(str(csv_path))
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    if args.search:
        result = search_by_keyword(metadata, args.search)
        if not args.quiet:
            print(f"\n搜索关键词: '{args.search}'")
            print(f"匹配的 insight_sid ({len(result['matched_insight_sids'])} 个):")
            for sid in result['matched_insight_sids']:
                print(f"  - {sid}")
            print(f"\n匹配的 legend ({len(result['matched_legends'])} 个):")
            for legend in result['matched_legends']:
                print(f"  - {legend}")
            
            if result['matched_insight_sids']:
                print(f"\n可用于 single_analysis.py 的参数:")
                print(f"  --insight-sids {' '.join(result['matched_insight_sids'])}")
            if result['matched_legends']:
                print(f"\n  --legends \"{result['matched_legends'][0]}\"")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return
    
    if args.insights_only:
        output = {
            "total": metadata['total_insights'],
            "insights": [
                {"insight_sid": i['insight_sid'], "insight_name": i['insight_name'], "legend_count": i['legend_count']}
                for i in metadata['insights']
            ]
        }
    elif args.legends_only:
        output = {
            "total": metadata['total_legends'],
            "legends": metadata['legends']
        }
    else:
        output = metadata
    
    if not args.quiet:
        print(f"\n=== CSV 元数据提取 ===")
        print(f"文件: {csv_path}")
        print(f"图表数量: {metadata['total_insights']}")
        print(f"曲线数量: {metadata['total_legends']}")
        
        if not args.legends_only:
            print(f"\n图表列表 (insight):")
            for insight in metadata['insights']:
                print(f"  [{insight['insight_sid']}] {insight['insight_name']} ({insight['legend_count']} 条曲线)")
        
        if not args.insights_only and len(metadata['legends']) <= 20:
            print(f"\n曲线列表 (legend):")
            for legend in metadata['legends']:
                print(f"  - {legend}")
        elif not args.insights_only:
            print(f"\n曲线列表 (legend): 共 {len(metadata['legends'])} 条，使用 --legends-only 查看完整列表")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        if not args.quiet:
            print(f"\n已保存到: {args.output}")
    elif args.quiet:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()