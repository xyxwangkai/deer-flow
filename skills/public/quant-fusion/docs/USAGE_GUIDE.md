# 量化融合系统使用指南

## 概述

量化融合系统是一个融合了Qlib、AlphaCouncil、TradingAgents三大项目的超级智能体系统，提供端到端的量化投资解决方案。

## 快速开始

### 1. 安装依赖

```bash
# 进入技能目录
cd /mnt/skills/public/quant-fusion

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置系统

编辑配置文件 `config/config.yaml`，根据需求调整以下设置：

```yaml
# 数据源配置
data_sources:
  stock_data:
    provider: "akshare"  # 数据提供商
    api_key: ""          # API密钥（如有需要）

# 模型配置
models:
  llm_providers:
    deepseek:
      enabled: true      # 启用DeepSeek
      api_key: "your_api_key_here"

# 交易配置
trading:
  broker:
    type: "simulation"   # 模拟交易
    # type: "real"       # 实盘交易（需配置券商接口）
```

### 3. 运行系统

#### 方式一：命令行接口

```bash
# 分析股票
python scripts/main.py analyze --symbols 000001 000002 --days 30

# 运行AlphaCouncil多智能体系统
python scripts/main.py council --symbols 600519 000858

# 执行交易策略
python scripts/main.py trade --strategy momentum --symbols 000001 000002 --capital 100000

# 风险评估
python scripts/main.py risk --portfolio '{"000001":0.5,"000002":0.5}'
```

#### 方式二：Python API

```python
import asyncio
from quant_fusion import QuantFusionSystem

async def main():
    # 初始化系统
    system = QuantFusionSystem("config/config.yaml")
    
    # 分析股票
    result = await system.run_full_analysis({
        "symbols": ["000001.SZ", "000002.SZ"],
        "timeframe": "1d",
        "days": 30
    })
    
    # 执行交易
    if result["trading_signals"]:
        execution_result = await system.execute_trades(
            result["trading_signals"],
            capital=100000
        )
        print(f"交易执行结果: {execution_result}")

asyncio.run(main())
```

## 核心功能详解

### 1. 多智能体分析系统

系统包含12个专业智能体角色：

```python
from agents.council import AlphaCouncilSystem, AgentRole

# 初始化AlphaCouncil系统
council = AlphaCouncilSystem()

# 运行委员会决策流程
result = await council.run_committee_decision(["000001.SZ"])

# 查看决策结果
print(f"决策: {result['decision']['action']}")
print(f"置信度: {result['decision']['confidence']:.2%}")
print(f"理由: {result['decision']['reason']}")
```

**智能体角色包括：**
- 📊 基本面分析师：分析财务报表、估值模型
- 📈 技术面分析师：图表分析、技术指标
- 😊 情绪面分析师：新闻情绪、社交媒体分析
- 💰 资金面分析师：资金流向、机构持仓
- 🌍 宏观面分析师：宏观经济、政策分析
- 🛡️ 风控总监：风险评估、合规审查
- 👔 整合总监：综合各分析师报告
- 🏢 总经理：最终投资决策
- 💼 交易员：执行交易计划

### 2. Qlib风格数据管理

```python
from data_manager import DataManager, RDAAgent

# 数据管理器
data_manager = DataManager()

# 获取股票数据
stock_data = await data_manager.get_stock_data(
    symbol="000001.SZ",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 技术指标计算
indicators = await data_manager.calculate_technical_indicators(
    stock_data,
    indicators=["RSI", "MACD", "Bollinger"]
)

# 强化学习因子挖掘
rda_agent = RDAAgent()
factors = await rda_agent.discover_factors(
    universe=["000001.SZ", "000002.SZ"],
    target="return_5d"
)
```

### 3. TradingAgents风格交易执行

```python
from trading_executor import TradingExecutor, BrokerType

# 创建交易执行器
executor = TradingExecutor(broker_type=BrokerType.SIMULATION)

# 创建账户
account = await executor.create_account(
    account_id="my_account",
    initial_balance=100000.0
)

# 下单
order = await executor.place_order(
    account_id="my_account",
    symbol="000001.SZ",
    action="BUY",
    quantity=100,
    price=10.0,
    order_type="LIMIT"
)

# 查询仓位
positions = await executor.get_positions("my_account")
```

### 4. 风险管理

```python
from risk_management import RiskManager

# 创建风险管理器
risk_manager = RiskManager()

# 投资组合风险评估
portfolio = {"000001.SZ": 0.4, "000002.SZ": 0.3, "000858.SZ": 0.3}
risk_metrics = await risk_manager.assess_portfolio_risk(portfolio)

print(f"VaR (95%): {risk_metrics.var_95:.2%}")
print(f"最大回撤: {risk_metrics.max_drawdown:.2%}")
print(f"夏普比率: {risk_metrics.sharpe_ratio:.2f}")

# 压力测试
stress_results = await risk_manager.run_stress_tests(
    portfolio,
    scenarios=["crash_2008", "covid_2020"]
)
```

## 高级功能

### 1. 自定义策略

```python
from core import QuantFusionSystem

class MyCustomStrategy:
    async def generate_signals(self, system, data):
        # 自定义信号生成逻辑
        signals = []
        
        # 使用系统内置分析器
        analysis_result = await system.run_full_analysis({
            "symbols": data["symbols"],
            "days": data["days"]
        })
        
        # 基于分析结果生成信号
        for stock_analysis in analysis_result["analysis_results"].values():
            if self._meets_criteria(stock_analysis):
                signals.append(self._create_signal(stock_analysis))
        
        return signals
    
    def _meets_criteria(self, analysis):
        # 自定义筛选条件
        avg_score = sum(a.score for a in analysis) / len(analysis)
        return avg_score > 70
    
    def _create_signal(self, analysis):
        # 创建交易信号
        return {
            "symbol": analysis[0].symbol,
            "action": "BUY",
            "price": analysis[0].price,
            "quantity": 100,
            "reason": "综合评分高"
        }

# 使用自定义策略
system = QuantFusionSystem()
strategy = MyCustomStrategy()
signals = await strategy.generate_signals(system, {
    "symbols": ["000001.SZ", "000002.SZ"],
    "days": 30
})
```

### 2. 实时监控

```python
import asyncio
from datetime import datetime

async def real_time_monitor(system, symbols, update_interval=60):
    """实时监控股票"""
    print(f"开始实时监控: {symbols}")
    
    while True:
        try:
            # 获取最新数据
            analysis_result = await system.run_full_analysis({
                "symbols": symbols,
                "timeframe": "1m",
                "days": 1
            })
            
            # 生成信号
            signals = analysis_result.get("trading_signals", [])
            
            if signals:
                print(f"[{datetime.now()}] 检测到交易信号:")
                for signal in signals:
                    print(f"  {signal.symbol}: {signal.action} @ ¥{signal.price:.2f}")
                
                # 自动执行交易（可选）
                # await system.execute_trades(signals, capital=10000)
            
            await asyncio.sleep(update_interval)
            
        except Exception as e:
            print(f"监控错误: {e}")
            await asyncio.sleep(10)

# 启动监控
asyncio.create_task(real_time_monitor(system, ["000001.SZ"]))
```

### 3. 绩效分析

```python
from core import QuantFusionSystem

async def analyze_performance(system, start_date, end_date):
    """历史绩效分析"""
    
    # 获取历史数据
    historical_data = await system.data_service.get_historical_data(
        symbols=["000001.SZ", "000002.SZ"],
        start_date=start_date,
        end_date=end_date
    )
    
    # 回测策略
    backtest_results = []
    for date in historical_data.dates:
        # 模拟每日决策
        daily_analysis = await system.run_full_analysis({
            "symbols": ["000001.SZ", "000002.SZ"],
            "end_date": date,
            "days": 30
        })
        
        # 记录决策
        backtest_results.append({
            "date": date,
            "analysis": daily_analysis,
            "signals": daily_analysis.get("trading_signals", [])
        })
    
    # 计算绩效指标
    performance = await system._calculate_performance(
        trades=backtest_results,
        positions=[],
        initial_capital=100000
    )
    
    return performance
```

## 配置文件详解

### 主要配置项

```yaml
# config/config.yaml

data_sources:
  stock_data:
    provider: "akshare"      # 数据提供商：akshare, tushare, baostock
    api_key: ""              # API密钥
    update_frequency: "1m"   # 更新频率：1m, 5m, 1d
  
  market_data:
    real_time: true          # 是否启用实时数据
    sources:                 # 数据源列表
      - "东方财富"
      - "新浪财经"

models:
  llm_providers:
    deepseek:
      enabled: true          # 启用DeepSeek
      api_key: ""            # DeepSeek API密钥
      model: "deepseek-chat" # 模型名称
  
  quant_models:
    qlib_enabled: true       # 启用Qlib
    alpha_factors:           # Alpha因子
      - "momentum"
      - "value"
      - "quality"

trading:
  broker:
    type: "simulation"       # 交易类型：simulation, real
    commission: 0.0003       # 佣金费率
  
  risk_management:
    max_position_size: 0.1   # 最大仓位比例
    max_daily_loss: 0.05     # 最大日亏损
    stop_loss: 0.03          # 止损比例

agents:
  analysts_count: 5          # 分析师数量
  enable_parallel_analysis: true  # 启用并行分析
  decision_threshold: 0.7    # 决策阈值
```

## 故障排除

### 常见问题

1. **数据获取失败**
   ```
   错误：无法连接到数据源
   解决方案：
   1. 检查网络连接
   2. 确认API密钥正确
   3. 尝试更换数据提供商
   ```

2. **模型加载失败**
   ```
   错误：无法加载Qlib模型
   解决方案：
   1. 确认已安装Qlib: pip install pyqlib
   2. 检查Qlib数据路径配置
   3. 运行Qlib初始化脚本
   ```

3. **交易执行失败**
   ```
   错误：下单被拒绝
   解决方案：
   1. 检查账户余额
   2. 确认交易时间（非交易时间无法下单）
   3. 检查价格限制（涨跌停限制）
   ```

4. **内存不足**
   ```
   错误：内存溢出
   解决方案：
   1. 减少分析股票数量
   2. 缩短分析时间范围
   3. 启用数据缓存
   ```

### 调试模式

启用调试日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或者修改配置文件
# logging:
#   level: "DEBUG"
```

## 最佳实践

### 1. 数据管理
- 定期清理缓存数据
- 使用增量更新减少数据加载时间
- 配置数据备份策略

### 2. 风险控制
- 设置合理的止损止盈
- 分散投资组合
- 定期进行压力测试

### 3. 性能优化
- 使用异步编程提高并发性能
- 启用数据缓存减少重复计算
- 定期优化模型参数

### 4. 监控告警
- 设置关键指标监控
- 配置异常告警
- 定期生成绩效报告

## API参考

### 核心类

#### QuantFusionSystem
```python
class QuantFusionSystem:
    async def run_full_analysis(config: Dict) -> Dict
    async def execute_trades(signals: List, capital: float) -> Dict
    async def get_system_status() -> Dict
```

#### DataManager
```python
class DataManager:
    async def get_stock_data(symbol: str, **kwargs) -> StockData
    async def calculate_technical_indicators(data, indicators: List) -> Dict
    async def update_cache() -> bool
```

#### AlphaCouncilSystem
```python
class AlphaCouncilSystem:
    async def run_committee_decision(symbols: List) -> Dict
    async def get_agent_insights(agent_id: str) -> Dict
    async def simulate_market_scenario(scenario: str) -> Dict
```

#### TradingExecutor
```python
class TradingExecutor:
    async def place_order(**kwargs) -> Order
    async def get_account_info(account_id: str) -> Account
    async def cancel_order(order_id: str) -> bool
```

#### RiskManager
```python
class RiskManager:
    async def assess_portfolio_risk(portfolio: Dict) -> RiskMetrics
    async def run_stress_tests(portfolio: Dict, scenarios: List) -> Dict
    async def check_risk_limits(positions: List) -> List[RiskAlert]
```

## 示例项目

### 示例1：简单的选股策略
```python
# examples/simple_stock_selection.py
import asyncio
from quant_fusion import QuantFusionSystem

async def simple_stock_selection():
    system = QuantFusionSystem()
    
    # 候选股票池
    candidate_symbols = ["000001.SZ", "000002.SZ", "000858.SZ", "600519.SH"]
    
    # 分析所有候选股票
    results = []
    for symbol in candidate_symbols:
        result = await system.run_full_analysis({
            "symbols": [symbol],
            "days": 30
        })
        
        # 计算综合评分
        avg_score = sum(
            a.score for a in result["analysis_results"].get(symbol, [])
        ) / len(result["analysis_results"].get(symbol, [])) if result["analysis_results"].get(symbol) else 0
        
        results.append({
            "symbol": symbol,
            "score": avg_score,
            "signals": result.get("trading_signals", [])
        })
    
    # 按评分排序
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 选择前3名
    selected = results[:3]
    print("选股结果:")
    for stock in selected:
        print(f"  {stock['symbol']}: 评分 {stock['score']:.1f}")
    
    return selected

asyncio.run(simple_stock_selection())
```

### 示例2：自动化交易机器人
```python
# examples/auto_trading_bot.py
import asyncio
import schedule
import time
from datetime import datetime
from quant_fusion import QuantFusionSystem

class AutoTradingBot:
    def __init__(self):
        self.system = QuantFusionSystem()
        self.running = False
    
    async def daily_trading_routine(self):
        """每日交易流程"""
        print(f"[{datetime.now()}] 开始每日交易流程")
        
        # 1. 市场分析
        analysis_result = await self.system.run_full_analysis({
            "symbols": self.get_watchlist(),
            "days": 30
        })
        
        # 2. 生成交易信号
        signals = analysis_result.get("trading_signals", [])
        
        if not signals:
            print("  未生成交易信号，跳过交易")
            return
        
        # 3. 执行交易
        execution_result = await self.system.execute_trades(
            signals,
            capital=50000
        )
        
        # 4. 记录交易
        self.log_trading_result(execution_result)
        
        print(f"  交易完成: {len(signals)} 个信号")
    
    def get_watchlist(self):
        """获取监控股票列表"""
        return ["000001.SZ", "000002.SZ", "000858.SZ"]
    
    def log_trading_result(self, result):
        """记录交易结果"""
        with open("trading_log.csv", "a") as f:
            f.write(f"{datetime.now()},{result['performance'].get('total_return', 0)}\n")
    
    async def run(self):
        """运行交易机器人"""
        self.running = True
        
        # 设置定时任务
        schedule.every().day.at("09:30").do(
            lambda: asyncio.create_task(self.daily_trading_routine())
        )
        
        print("交易机器人已启动，等待交易时间...")
        
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # 每分钟检查一次

# 启动机器人
bot = AutoTradingBot()
asyncio.run(bot.run())
```

## 支持与反馈

如有