#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化融合系统 - 主入口文件
融合Qlib、AlphaCouncil、TradingAgents的超级智能体系统
"""

import asyncio
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core import (
    QuantFusionSystem, 
    StockData, 
    AnalysisResult, 
    TradingSignal,
    MarketType,
    AnalysisType
)
from data_manager import DataManager, RDAAgent
from trading_executor import TradingExecutor, Order, Position, Account, BrokerType
from risk_management import RiskManager, RiskMetrics, RiskLimit, RiskAlert
from agents.council import AlphaCouncilSystem, AgentRole


class QuantFusionCLI:
    """量化融合系统命令行接口"""
    
    def __init__(self):
        self.system = None
        self.config_path = "config/config.yaml"
        
    async def initialize(self):
        """初始化系统"""
        print("🚀 初始化量化融合系统...")
        
        # 创建配置目录
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # 如果配置文件不存在，创建默认配置
        if not Path(self.config_path).exists():
            self._create_default_config()
        
        # 初始化系统
        self.system = QuantFusionSystem(self.config_path)
        print("✅ 系统初始化完成")
        
    def _create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "data_sources": {
                "stock_data": {
                    "provider": "akshare",
                    "api_key": "",
                    "update_frequency": "1m"
                },
                "market_data": {
                    "real_time": True,
                    "sources": ["东方财富", "新浪财经"]
                },
                "economic_data": {
                    "sources": ["国家统计局", "央行"],
                    "update_frequency": "1d"
                }
            },
            "models": {
                "llm_providers": {
                    "openai": {"enabled": False, "api_key": ""},
                    "gemini": {"enabled": False, "api_key": ""},
                    "deepseek": {"enabled": True, "api_key": ""},
                    "qwen": {"enabled": True, "api_key": ""}
                },
                "quant_models": {
                    "qlib_enabled": True,
                    "alpha_factors": ["momentum", "value", "quality", "growth"],
                    "model_types": ["lightgbm", "xgboost", "deep_learning"]
                }
            },
            "trading": {
                "broker": {
                    "type": "simulation",
                    "commission": 0.0003,
                    "slippage": 0.0001
                },
                "risk_management": {
                    "max_position_size": 0.1,
                    "max_daily_loss": 0.05,
                    "stop_loss": 0.03,
                    "take_profit": 0.05,
                    "max_leverage": 1.0
                },
                "execution": {
                    "algorithm": "TWAP",
                    "max_slippage": 0.001,
                    "min_trade_size": 100
                }
            },
            "agents": {
                "analysts_count": 5,
                "enable_parallel_analysis": True,
                "decision_threshold": 0.7,
                "committee_size": 12,
                "enable_alpha_council": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/quant_fusion.log",
                "console": True
            }
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            import yaml
            yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"📁 创建默认配置文件: {self.config_path}")
    
    async def analyze_stocks(self, symbols: List[str], 
                           timeframe: str = "1d",
                           days: int = 30) -> Dict[str, Any]:
        """
        分析股票
        
        Args:
            symbols: 股票代码列表
            timeframe: 时间周期
            days: 分析天数
            
        Returns:
            分析结果
        """
        if not self.system:
            await self.initialize()
        
        print(f"📊 开始分析股票: {', '.join(symbols)}")
        print(f"   时间周期: {timeframe}, 分析天数: {days}天")
        
        # 准备分析配置
        analysis_config = {
            "symbols": symbols,
            "timeframe": timeframe,
            "start_date": datetime.now() - timedelta(days=days),
            "end_date": datetime.now(),
            "analysis_types": ["fundamental", "technical", "sentiment", "capital_flow", "macro"]
        }
        
        # 运行完整分析
        result = await self.system.run_full_analysis(analysis_config)
        
        # 保存结果
        self._save_analysis_result(result, symbols)
        
        return result
    
    async def run_alpha_council(self, symbols: List[str]) -> Dict[str, Any]:
        """
        运行AlphaCouncil多智能体系统
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            AlphaCouncil分析结果
        """
        print(f"🤖 启动AlphaCouncil多智能体系统...")
        print(f"   分析股票: {', '.join(symbols)}")
        
        # 初始化AlphaCouncil系统
        council_system = AlphaCouncilSystem()
        
        # 运行委员会决策流程
        result = await council_system.run_committee_decision(symbols)
        
        # 保存结果
        output_file = f"outputs/alpha_council_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(output_file).parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 AlphaCouncil结果已保存: {output_file}")
        return result
    
    async def execute_trading_strategy(self, strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行交易策略
        
        Args:
            strategy_config: 策略配置
            
        Returns:
            交易执行结果
        """
        print("💼 执行交易策略...")
        
        # 解析配置
        symbols = strategy_config.get("symbols", [])
        capital = strategy_config.get("capital", 100000)
        strategy_type = strategy_config.get("strategy_type", "momentum")
        
        print(f"   策略类型: {strategy_type}")
        print(f"   投资金额: ¥{capital:,.2f}")
        print(f"   目标股票: {', '.join(symbols)}")
        
        # 分析股票获取交易信号
        analysis_result = await self.analyze_stocks(symbols)
        
        if "trading_signals" not in analysis_result or not analysis_result["trading_signals"]:
            print("⚠️  未生成交易信号")
            return {"error": "未生成交易信号"}
        
        # 执行交易
        execution_result = await self.system.execute_trades(
            analysis_result["trading_signals"],
            capital
        )
        
        # 保存交易记录
        self._save_trading_result(execution_result)
        
        return execution_result
    
    async def risk_assessment(self, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """
        投资组合风险评估
        
        Args:
            portfolio: 投资组合 {股票代码: 权重}
            
        Returns:
            风险评估结果
        """
        print("🛡️  进行投资组合风险评估...")
        
        # 初始化风险管理器
        risk_manager = RiskManager()
        
        # 计算风险指标
        risk_metrics = await risk_manager.assess_portfolio_risk(portfolio)
        
        # 生成风险报告
        risk_report = {
            "portfolio": portfolio,
            "risk_metrics": risk_metrics.__dict__ if hasattr(risk_metrics, '__dict__') else risk_metrics,
            "recommendations": await risk_manager.generate_risk_recommendations(risk_metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存风险报告
        output_file = f"outputs/risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(output_file).parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(risk_report, f, ensure_ascii=False, indent=2)
        
        print(f"💾 风险评估报告已保存: {output_file}")
        return risk_report
    
    def _save_analysis_result(self, result: Dict[str, Any], symbols: List[str]):
        """保存分析结果"""
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{'_'.join(symbols)}_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 分析结果已保存: {filepath}")
        
        # 生成摘要报告
        self._generate_summary_report(result, filepath)
    
    def _generate_summary_report(self, result: Dict[str, Any], json_path: Path):
        """生成摘要报告"""
        summary_path = Path(str(json_path).replace('.json', '_summary.md'))
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# 量化分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if "stock_data" in result:
                f.write(f"## 分析股票\n")
                for stock in result["stock_data"]:
                    if hasattr(stock, 'symbol'):
                        f.write(f"- {stock.symbol}: {stock.name}\n")
            
            if "analysis_results" in result:
                f.write(f"\n## 分析结果\n")
                for symbol, analyses in result["analysis_results"].items():
                    f.write(f"\n### {symbol}\n")
                    for analysis in analyses:
                        if hasattr(analysis, 'analysis_type'):
                            f.write(f"- {analysis.analysis_type}: 评分 {analysis.score:.1f} (置信度 {analysis.confidence:.2f})\n")
            
            if "trading_signals" in result:
                f.write(f"\n## 交易信号\n")
                for signal in result["trading_signals"]:
                    if hasattr(signal, 'action'):
                        f.write(f"- {signal.symbol}: {signal.action} @ ¥{signal.price:.2f} ({signal.reason})\n")
            
            if "final_decision" in result:
                f.write(f"\n## 最终决策\n")
                f.write(f"```json\n{json.dumps(result['final_decision'], ensure_ascii=False, indent=2)}\n```\n")
        
        print(f"📋 摘要报告已生成: {summary_path}")
    
    def _save_trading_result(self, result: Dict[str, Any]):
        """保存交易结果"""
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trading_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 交易记录已保存: {filepath}")
        
        # 生成交易绩效报告
        if "performance" in result:
            perf_path = Path(str(filepath).replace('.json', '_performance.md'))
            with open(perf_path, 'w', encoding='utf-8') as f:
                f.write(f"# 交易绩效报告\n\n")
                f.write(f"**交易时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## 绩效指标\n")
                for key, value in result["performance"].items():
                    if isinstance(value, float):
                        f.write(f"- {key}: {value:.4f}\n")
                    else:
                        f.write(f"- {key}: {value}\n")
            
            print(f"📈 绩效报告已生成: {perf_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="量化融合系统 - 融合Qlib、AlphaCouncil、TradingAgents的超级智能体系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s analyze --symbols 000001 000002          # 分析股票
  %(prog)s council --symbols 600519 000858          # 运行AlphaCouncil
  %(prog)s trade --strategy momentum --capital 100000 # 执行交易策略
  %(prog)s risk --portfolio '{"000001":0.5,"000002":0.5}' # 风险评估
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 分析命令
    analyze_parser = subparsers.add_parser("analyze", help="分析股票")
    analyze_parser.add_argument("--symbols", nargs="+", required=True, help="股票代码列表")
    analyze_parser.add_argument("--timeframe", default="1d", help="时间周期 (1m, 5m, 1d, 1w)")
    analyze_parser.add_argument("--days", type=int, default=30, help="分析天数")
    
    # AlphaCouncil命令
    council_parser = subparsers.add_parser("council", help="运行AlphaCouncil多智能体系统")
    council_parser.add_argument("--symbols", nargs="+", required=True, help="股票代码列表")
    
    # 交易命令
    trade_parser = subparsers.add_parser("trade", help="执行交易策略")
    trade_parser.add_argument("--strategy", required=True, 
                            choices=["momentum", "mean_reversion", "trend_following", "arbitrage"],
                            help="策略类型")
    trade_parser.add_argument("--symbols", nargs="+", required=True, help="股票代码列表")
    trade_parser.add_argument("--capital", type=float, default=100000, help="投资金额")
    
    # 风险评估命令
    risk_parser = subparsers.add_parser("risk", help="投资组合风险评估")
    risk_parser.add_argument("--portfolio", required=True, help="投资组合JSON，如 '{\"000001\":0.5,\"000002\":0.5}'")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 创建CLI实例
    cli = QuantFusionCLI()
    
    try:
        # 执行命令
        if args.command == "analyze":
            asyncio.run(cli.analyze_stocks(
                symbols=args.symbols,
                timeframe=args.timeframe,
                days=args.days
            ))
            
        elif args.command == "council":
            asyncio.run(cli.run_alpha_council(symbols=args.symbols))
            
        elif args.command == "trade":
            strategy_config = {
                "strategy_type": args.strategy,
                "symbols": args.symbols,
                "capital": args.capital
            }
            asyncio.run(cli.execute_trading_strategy(strategy_config))
            
        elif args.command == "risk":
            try:
                portfolio = json.loads(args.portfolio)
            except json.JSONDecodeError:
                print(f"❌ 投资组合格式错误: {args.portfolio}")
                print("请使用JSON格式，例如: '{\"000001\":0.5,\"000002\":0.5}'")
                sys.exit(1)
            
            asyncio.run(cli.risk_assessment(portfolio))
            
    except KeyboardInterrupt:
        print("\n\n👋 用户中断操作")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()