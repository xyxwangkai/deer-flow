#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化融合系统测试脚本
测试核心功能是否正常工作
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用绝对导入
from core import QuantFusionSystem, MarketType, AnalysisType
from data_manager import DataManager
from trading_executor import TradingExecutor, BrokerType
from risk_management import RiskManager
from agents.council import AlphaCouncilSystem, AgentRole


async def test_data_manager():
    """测试数据管理器"""
    print("🧪 测试数据管理器...")
    
    try:
        # 创建数据管理器
        data_manager = DataManager({
            "data_sources": {
                "stock_data": {
                    "provider": "akshare",
                    "api_key": "",
                    "update_frequency": "1m"
                }
            }
        })
        
        # 测试数据获取
        symbol = "000001.SZ"
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        print(f"   获取股票历史数据: {symbol}")
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        historical_data = await data_manager.get_stock_history(
            symbol=symbol,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        if not historical_data.empty:
            print(f"   ✅ 数据获取成功")
            print(f"      股票: {symbol}")
            print(f"      数据条数: {len(historical_data)}")
            print(f"      时间范围: {historical_data.index[0]} 到 {historical_data.index[-1]}")
            return True
        else:
            print("   ❌ 数据获取失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


async def test_alpha_council():
    """测试AlphaCouncil系统"""
    print("🧪 测试AlphaCouncil多智能体系统...")
    
    try:
        # 创建AlphaCouncil系统
        council_system = AlphaCouncilSystem({
            "agents": {
                "analyst_fundamental": {"initial_confidence": 0.7},
                "analyst_technical": {"initial_confidence": 0.7},
                "analyst_sentiment": {"initial_confidence": 0.7},
                "analyst_capital": {"initial_confidence": 0.7},
                "analyst_macro": {"initial_confidence": 0.7},
                "analyst_risk": {"initial_confidence": 0.7},
                "director_integration": {"initial_confidence": 0.8},
                "director_risk": {"initial_confidence": 0.8},
                "manager_general": {"initial_confidence": 0.9}
            }
        })
        
        # 测试委员会决策
        symbols = ["000001.SZ", "000002.SZ"]
        print(f"   分析股票: {symbols}")
        
        result = await council_system.run_committee_decision(symbols)
        
        if result and "decision" in result:
            print(f"   ✅ AlphaCouncil测试成功")
            print(f"      决策结果: {result['decision']['action']}")
            print(f"      置信度: {result['decision']['confidence']:.2f}")
            return True
        else:
            print("   ❌ AlphaCouncil测试失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


async def test_trading_executor():
    """测试交易执行器"""
    print("🧪 测试交易执行器...")
    
    try:
        # 创建交易执行器
        executor = TradingExecutor({
            "broker": {
                "type": "simulation",
                "commission": 0.0003
            }
        })
        
        # 创建模拟账户
        account = await executor.create_account(
            account_id="test_account",
            initial_capital=100000.0
        )
        
        print(f"   创建账户: {account.account_id}")
        print(f"   初始余额: ¥{account.balance:,.2f}")
        
        # 测试下单
        order = await executor.place_order(
            account_id="test_account",
            order_data={
                "symbol": "000001.SZ",
                "action": "BUY",
                "order_type": "MARKET",
                "quantity": 100,
                "price": 10.0
            }
        )
        
        if order and order.order_id:
            print(f"   ✅ 下单成功")
            print(f"      订单ID: {order.order_id}")
            print(f"      状态: {order.status}")
            return True
        else:
            print("   ❌ 下单失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


async def test_risk_management():
    """测试风险管理"""
    print("🧪 测试风险管理...")
    
    try:
        # 创建风险管理器
        risk_manager = RiskManager({
            "risk_management": {
                "max_position_size": 0.1,
                "max_daily_loss": 0.05,
                "max_concentration": 0.3,
                "var_confidence": 0.95,
                "stress_scenarios": ["market_crash", "liquidity_crisis"]
            }
        })
        
        # 测试投资组合风险评估
        portfolio = {
            "000001.SZ": 0.4,
            "000002.SZ": 0.3,
            "000858.SZ": 0.3
        }
        
        # 创建模拟市场数据
        market_data = {
            "000001.SZ": {
                "price": 10.5,
                "volume": 1000000,
                "volatility": 0.2,
                "beta": 1.1
            },
            "000002.SZ": {
                "price": 25.3,
                "volume": 500000,
                "volatility": 0.15,
                "beta": 0.9
            },
            "000858.SZ": {
                "price": 150.0,
                "volume": 200000,
                "volatility": 0.25,
                "beta": 1.3
            }
        }
        
        print(f"   评估投资组合: {portfolio}")
        risk_assessment = await risk_manager.assess_portfolio_risk(portfolio, market_data)
        
        if risk_assessment and "risk_metrics" in risk_assessment:
            print(f"   ✅ 风险评估成功")
            risk_metrics = risk_assessment["risk_metrics"]
            print(f"      VaR (95%): {risk_metrics.get('var_95', 0):.2%}")
            print(f"      最大回撤: {risk_metrics.get('max_drawdown', 0):.2%}")
            print(f"      夏普比率: {risk_metrics.get('sharpe_ratio', 0):.2f}")
            return True
        else:
            print("   ❌ 风险评估失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False


async def test_full_system():
    """测试完整系统"""
    print("🧪 测试完整量化融合系统...")
    
    try:
        # 创建系统实例
        system = QuantFusionSystem()
        
        # 测试分析流程
        analysis_config = {
            "symbols": ["000001.SZ"],
            "timeframe": "1d",
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now()
        }
        
        print(f"   运行完整分析流程...")
        result = await system.run_full_analysis(analysis_config)
        
        if result and "analysis_results" in result:
            print(f"   ✅ 系统测试成功")
            print(f"      分析股票数: {len(result.get('stock_data', []))}")
            print(f"      生成信号数: {len(result.get('trading_signals', []))}")
            
            # 如果有交易信号，测试执行
            if "trading_signals" in result and result["trading_signals"]:
                print(f"   测试交易执行...")
                execution_result = await system.execute_trades(
                    result["trading_signals"],
                    capital=50000
                )
                
                if "performance" in execution_result:
                    print(f"   ✅ 交易执行成功")
                    print(f"      总交易数: {execution_result['performance'].get('total_trades', 0)}")
                    print(f"      成功率: {execution_result['performance'].get('success_rate', 0):.2%}")
            
            return True
        else:
            print("   ❌ 系统测试失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🔬 开始量化融合系统测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各个模块测试
    test_results.append(("数据管理器", await test_data_manager()))
    print()
    
    test_results.append(("AlphaCouncil系统", await test_alpha_council()))
    print()
    
    test_results.append(("交易执行器", await test_trading_executor()))
    print()
    
    test_results.append(("风险管理", await test_risk_management()))
    print()
    
    test_results.append(("完整系统", await test_full_system()))
    print()
    
    # 输出测试结果
    print("=" * 50)
    print("📊 测试结果汇总:")
    print("=" * 50)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print("=" * 50)
    print(f"总计: {passed_tests}/{total_tests} 个测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！系统功能正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查系统配置。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)