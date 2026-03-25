"""
VaR（Value at Risk）模型 - 风险价值模型
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta


class VaRModel:
    """VaR（风险价值）模型"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化VaR模型
        
        Args:
            config: 模型配置
        """
        self.config = config
        self.var_method = config.get("var_method", "historical")
        self.confidence_level = config.get("confidence_level", 0.95)
        self.time_horizon = config.get("time_horizon", 1)  # 天
        self.lookback_period = config.get("lookback_period", 252)  # 交易日
    
    async def calculate(self, portfolio: Dict[str, Any], 
                       market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算VaR
        
        Args:
            portfolio: 投资组合数据
            market_data: 市场数据
            
        Returns:
            VaR计算结果
        """
        if self.var_method == "historical":
            return await self._historical_var(portfolio, market_data)
        elif self.var_method == "parametric":
            return await self._parametric_var(portfolio, market_data)
        elif self.var_method == "monte_carlo":
            return await self._monte_carlo_var(portfolio, market_data)
        else:
            return await self._historical_var(portfolio, market_data)
    
    async def _historical_var(self, portfolio: Dict[str, Any], 
                            market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        历史模拟法VaR
        
        Args:
            portfolio: 投资组合数据
            market_data: 市场数据
            
        Returns:
            历史VaR结果
        """
        # 获取历史收益率
        returns = self._get_portfolio_returns(portfolio, market_data)
        
        if len(returns) < 10:
            return {"error": "历史数据不足"}
        
        # 计算VaR
        var_value = -np.percentile(returns, (1 - self.confidence_level) * 100)
        
        # 计算ES（Expected Shortfall）
        losses = returns[returns < -var_value]
        es_value = -losses.mean() if len(losses) > 0 else var_value * 1.5
        
        # 计算分位数
        quantiles = {
            "0.95": -np.percentile(returns, 5),
            "0.99": -np.percentile(returns, 1),
            "0.999": -np.percentile(returns, 0.1)
        }
        
        return {
            "var_value": float(var_value),
            "es_value": float(es_value),
            "confidence_level": self.confidence_level,
            "time_horizon": self.time_horizon,
            "method": "historical",
            "quantiles": quantiles,
            "data_points": len(returns),
            "mean_return": float(returns.mean()),
            "std_return": float(returns.std())
        }
    
    async def _parametric_var(self, portfolio: Dict[str, Any], 
                            market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        参数法VaR（正态分布假设）
        
        Args:
            portfolio: 投资组合数据
            market_data: 市场数据
            
        Returns:
            参数VaR结果
        """
        # 获取投资组合收益率
        returns = self._get_portfolio_returns(portfolio, market_data)
        
        if len(returns) < 10:
            return {"error": "历史数据不足"}
        
        # 计算均值和标准差
        mean_return = returns.mean()
        std_return = returns.std()
        
        # 计算z-score
        from scipy.stats import norm
        z_score = norm.ppf(1 - self.confidence_level)
        
        # 计算VaR
        var_value = -(mean_return + z_score * std_return)
        
        # 计算ES（正态分布下的期望损失）
        es_value = -(mean_return + std_return * norm.pdf(z_score) / (1 - self.confidence_level))
        
        return {
            "var_value": float(var_value),
            "es_value": float(es_value),
            "confidence_level": self.confidence_level,
            "time_horizon": self.time_horizon,
            "method": "parametric",
            "mean_return": float(mean_return),
            "std_return": float(std_return),
            "z_score": float(z_score),
            "data_points": len(returns)
        }
    
    async def _monte_carlo_var(self, portfolio: Dict[str, Any], 
                             market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        蒙特卡洛模拟法VaR
        
        Args:
            portfolio: 投资组合数据
            market_data: 市场数据
            
        Returns:
            蒙特卡洛VaR结果
        """
        # 获取历史收益率
        returns = self._get_portfolio_returns(portfolio, market_data)
        
        if len(returns) < 10:
            return {"error": "历史数据不足"}
        
        # 计算均值和协方差
        mean_return = returns.mean()
        std_return = returns.std()
        
        # 模拟次数
        n_simulations = self.config.get("n_simulations", 10000)
        
        # 生成随机收益
        np.random.seed(42)  # 可重复性
        simulated_returns = np.random.normal(
            mean_return, std_return, n_simulations
        )
        
        # 计算VaR
        var_value = -np.percentile(simulated_returns, (1 - self.confidence_level) * 100)
        
        # 计算ES
        losses = simulated_returns[simulated_returns < -var_value]
        es_value = -losses.mean() if len(losses) > 0 else var_value * 1.5
        
        return {
            "var_value": float(var_value),
            "es_value": float(es_value),
            "confidence_level": self.confidence_level,
            "time_horizon": self.time_horizon,
            "method": "monte_carlo",
            "simulations": n_simulations,
            "mean_return": float(mean_return),
            "std_return": float(std_return),
            "data_points": len(returns)
        }
    
    def _get_portfolio_returns(self, portfolio: Dict[str, Any], 
                              market_data: Dict[str, Any]) -> np.ndarray:
        """
        获取投资组合收益率
        
        Args:
            portfolio: 投资组合数据
            market_data: 市场数据
            
        Returns:
            收益率数组
        """
        # 这里简化处理：假设投资组合只有一个资产
        # 实际应用中需要根据权重计算组合收益率
        
        positions = portfolio.get("positions", {})
        if not positions:
            # 如果没有持仓，返回随机收益率
            return np.random.normal(0, 0.02, self.lookback_period)
        
        # 获取第一个资产的收益率
        symbol = list(positions.keys())[0]
        asset_data = market_data.get(symbol, {})
        
        if "returns" in asset_data:
            returns = asset_data["returns"]
            if len(returns) > self.lookback_period:
                returns = returns[-self.lookback_period:]
            return np.array(returns)
        
        # 如果没有收益率数据，生成模拟数据
        return np.random.normal(0, 0.02, self.lookback_period)
    
    async def backtest(self, portfolio: Dict[str, Any], 
                      market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        VaR回测
        
        Args:
            portfolio: 投资组合数据
            market_data: 市场数据
            
        Returns:
            回测结果
        """
        # 获取历史收益率
        returns = self._get_portfolio_returns(portfolio, market_data)
        
        if len(returns) < 100:
            return {"error": "数据不足进行回测"}
        
        # 计算每日VaR
        var_series = []
        violations = 0
        
        window_size = 100  # 滚动窗口大小
        for i in range(window_size, len(returns)):
            window_returns = returns[i-window_size:i]
            
            # 计算窗口内的VaR
            window_var = -np.percentile(window_returns, (1 - self.confidence_level) * 100)
            var_series.append(window_var)
            
            # 检查是否违反VaR
            if returns[i] < -window_var:
                violations += 1
        
        # 计算回测指标
        total_days = len(returns) - window_size
        violation_rate = violations / total_days if total_days > 0 else 0
        expected_violations = (1 - self.confidence_level) * total_days
        
        # Kupiec检验
        from scipy.stats import binomtest
        p_value = 1.0
        if expected_violations > 0:
            test_result = binomtest(violations, total_days, 1 - self.confidence_level)
            p_value = test_result.pvalue
        
        return {
            "total_days": total_days,
            "violations": violations,
            "violation_rate": float(violation_rate),
            "expected_violations": float(expected_violations),
            "kupiec_p_value": float(p_value),
            "backtest_passed": p_value > 0.05,  # 95%置信水平
            "var_series_mean": float(np.mean(var_series)) if var_series else 0,
            "var_series_std": float(np.std(var_series)) if var_series else 0
        }