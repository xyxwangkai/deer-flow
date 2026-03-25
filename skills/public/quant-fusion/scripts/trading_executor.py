#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易执行器模块
基于TradingAgents的交易执行框架
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class BrokerType(Enum):
    """经纪商类型"""
    SIMULATION = "simulation"
    PAPER = "paper"
    REAL = "real"


@dataclass
class Order:
    """订单类"""
    order_id: str
    symbol: str
    action: str  # BUY, SELL, CANCEL
    order_type: str  # MARKET, LIMIT, STOP
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    limit_price: Optional[float] = None
    status: str = "PENDING"  # PENDING, FILLED, PARTIAL, CANCELLED, REJECTED
    filled_quantity: int = 0
    avg_fill_price: float = 0.0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    expiry: Optional[datetime] = None


@dataclass
class Position:
    """仓位类"""
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
@dataclass
class Account:
    """账户类"""
    account_id: str
    broker_type: BrokerType
    initial_capital: float
    current_capital: float
    positions: Dict[str, Position] = field(default_factory=dict)
    orders: Dict[str, Order] = field(default_factory=dict)
    trade_history: List[Dict] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def balance(self) -> float:
        """账户余额（与current_capital保持一致）"""
        return self.current_capital


class TradingExecutor:
    """交易执行器 - TradingAgents风格"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化交易执行器
        
        Args:
            config: 交易配置
        """
        self.config = config
        self.broker = None
        self.accounts = {}
        self.order_book = {}
        self.market_data = {}
        
        # 初始化经纪商
        self._init_broker()
        
        logger.info("交易执行器初始化完成")
    
    def _init_broker(self):
        """初始化经纪商"""
        broker_config = self.config.get("broker", {})
        broker_type = broker_config.get("type", "simulation")
        
        if broker_type == "simulation":
            from brokers.simulation_broker import SimulationBroker
            self.broker = SimulationBroker(broker_config)
        elif broker_type == "paper":
            from brokers.paper_broker import PaperBroker
            self.broker = PaperBroker(broker_config)
        elif broker_type == "real":
            # 这里可以集成真实的经纪商API
            logger.warning("实盘交易需要配置真实的经纪商API")
            from brokers.simulation_broker import SimulationBroker
            self.broker = SimulationBroker(broker_config)
        else:
            from brokers.simulation_broker import SimulationBroker
            self.broker = SimulationBroker(broker_config)
        
        logger.info(f"使用经纪商类型: {broker_type}")
    
    async def create_account(self, account_id: str, initial_capital: float = 100000) -> Account:
        """
        创建交易账户
        
        Args:
            account_id: 账户ID
            initial_capital: 初始资金
            
        Returns:
            账户对象
        """
        if account_id in self.accounts:
            logger.warning(f"账户已存在: {account_id}")
            return self.accounts[account_id]
        
        account = Account(
            account_id=account_id,
            broker_type=BrokerType(self.config["broker"]["type"]),
            initial_capital=initial_capital,
            current_capital=initial_capital
        )
        
        self.accounts[account_id] = account
        logger.info(f"创建账户成功: {account_id}, 初始资金: {initial_capital}")
        
        return account
    
    async def place_order(self, account_id: str, order_data: Dict[str, Any]) -> Order:
        """
        下单
        
        Args:
            account_id: 账户ID
            order_data: 订单数据
            
        Returns:
            订单对象
        """
        if account_id not in self.accounts:
            logger.error(f"账户不存在: {account_id}")
            raise ValueError(f"账户不存在: {account_id}")
        
        account = self.accounts[account_id]
        
        # 创建订单
        order = Order(
            order_id=f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(account.orders)}",
            symbol=order_data.get("symbol"),
            action=order_data.get("action", "BUY").upper(),
            order_type=order_data.get("order_type", "MARKET").upper(),
            quantity=order_data.get("quantity", 0),
            price=order_data.get("price"),
            stop_price=order_data.get("stop_price"),
            limit_price=order_data.get("limit_price"),
            expiry=order_data.get("expiry")
        )
        
        # 检查订单有效性
        if not await self._validate_order(account, order):
            order.status = "REJECTED"
            account.orders[order.order_id] = order
            logger.warning(f"订单被拒绝: {order.order_id}")
            return order
        
        # 提交到经纪商
        try:
            # 根据经纪商类型调用不同的方法
            if account.broker_type == BrokerType.SIMULATION:
                # 使用simulation_broker的place_order方法
                from brokers.simulation_broker import OrderType as SimOrderType
                
                # 转换订单类型
                if order.order_type == "MARKET":
                    order_type = SimOrderType.MARKET
                elif order.order_type == "LIMIT":
                    order_type = SimOrderType.LIMIT
                elif order.order_type == "STOP":
                    order_type = SimOrderType.STOP
                else:
                    order_type = SimOrderType.MARKET
                
                # 转换买卖方向
                side = "buy" if order.action == "BUY" else "sell"
                
                # 调用place_order
                filled_order = await self.broker.place_order(
                    account_id=account.account_id,
                    symbol=order.symbol,
                    side=side,
                    quantity=order.quantity,
                    order_type=order_type,
                    price=order.price
                )
                
                # 将返回的Order对象转换为本地的Order对象
                filled_local_order = Order(
                    order_id=filled_order.order_id,
                    symbol=filled_order.symbol,
                    action=order.action,
                    order_type=order.order_type,
                    quantity=filled_order.quantity,
                    price=filled_order.price,
                    status=filled_order.status.value.upper(),
                    filled_quantity=filled_order.filled_quantity,
                    avg_fill_price=filled_order.filled_price or 0.0,
                    timestamp=filled_order.created_at
                )
                
                # 更新账户状态
                account.orders[filled_local_order.order_id] = filled_local_order
                
                if filled_local_order.status == "FILLED":
                    await self._update_account_after_fill(account, filled_local_order)
                
                logger.info(f"订单执行完成: {filled_local_order.order_id}, 状态: {filled_local_order.status}")
                return filled_local_order
            else:
                # 其他经纪商类型
                filled_order = await self.broker.execute_order(account, order)
                
                # 更新账户状态
                account.orders[filled_order.order_id] = filled_order
                
                if filled_order.status == "FILLED":
                    await self._update_account_after_fill(account, filled_order)
                
                logger.info(f"订单执行完成: {filled_order.order_id}, 状态: {filled_order.status}")
                return filled_order
                
        except Exception as e:
            logger.error(f"订单执行失败 {order.order_id}: {e}")
            order.status = "REJECTED"
            account.orders[order.order_id] = order
            return order
    
    async def _validate_order(self, account: Account, order: Order) -> bool:
        """验证订单有效性"""
        # 检查资金
        if order.action == "BUY":
            estimated_cost = order.quantity * (order.price or 0)
            commission = estimated_cost * self.config["broker"].get("commission", 0.0003)
            total_cost = estimated_cost + commission
            
            if total_cost > account.current_capital:
                logger.warning(f"资金不足: 需要 {total_cost}, 可用 {account.current_capital}")
                return False
        
        # 检查数量
        if order.quantity <= 0:
            logger.warning("订单数量必须大于0")
            return False
        
        # 检查价格
        if order.order_type in ["LIMIT", "STOP"] and not order.price:
            logger.warning("限价单和止损单需要指定价格")
            return False
        
        return True
    
    async def _update_account_after_fill(self, account: Account, order: Order):
        """订单成交后更新账户"""
        if order.action == "BUY":
            # 更新资金
            cost = order.filled_quantity * order.avg_fill_price
            total_cost = cost + order.commission
            account.current_capital -= total_cost
            
            # 更新仓位
            symbol = order.symbol
            if symbol in account.positions:
                position = account.positions[symbol]
                # 计算新的平均价格
                total_quantity = position.quantity + order.filled_quantity
                total_value = (position.quantity * position.avg_price + 
                             order.filled_quantity * order.avg_fill_price)
                new_avg_price = total_value / total_quantity if total_quantity > 0 else 0
                
                position.quantity = total_quantity
                position.avg_price = new_avg_price
            else:
                account.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=order.filled_quantity,
                    avg_price=order.avg_fill_price,
                    current_price=order.avg_fill_price
                )
        
        elif order.action == "SELL":
            # 更新资金
            revenue = order.filled_quantity * order.avg_fill_price
            total_revenue = revenue - order.commission
            account.current_capital += total_revenue
            
            # 更新仓位
            symbol = order.symbol
            if symbol in account.positions:
                position = account.positions[symbol]
                
                # 计算已实现盈亏
                cost = order.filled_quantity * position.avg_price
                revenue = order.filled_quantity * order.avg_fill_price
                realized_pnl = revenue - cost - order.commission
                
                position.quantity -= order.filled_quantity
                position.realized_pnl += realized_pnl
                
                # 如果仓位为0，移除该仓位
                if position.quantity <= 0:
                    del account.positions[symbol]
        
        # 记录交易历史
        trade_record = {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "action": order.action,
            "quantity": order.filled_quantity,
            "price": order.avg_fill_price,
            "commission": order.commission,
            "timestamp": order.timestamp.isoformat(),
            "account_balance": account.current_capital
        }
        account.trade_history.append(trade_record)
    
    async def cancel_order(self, account_id: str, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            account_id: 账户ID
            order_id: 订单ID
            
        Returns:
            是否取消成功
        """
        if account_id not in self.accounts:
            logger.error(f"账户不存在: {account_id}")
            return False
        
        account = self.accounts[account_id]
        
        if order_id not in account.orders:
            logger.error(f"订单不存在: {order_id}")
            return False
        
        order = account.orders[order_id]
        
        if order.status not in ["PENDING", "PARTIAL"]:
            logger.warning(f"订单状态为 {order.status}，无法取消")
            return False
        
        # 请求经纪商取消订单
        try:
            success = await self.broker.cancel_order(order)
            if success:
                order.status = "CANCELLED"
                logger.info(f"订单取消成功: {order_id}")
            else:
                logger.warning(f"订单取消失败: {order_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"取消订单失败 {order_id}: {e}")
            return False
    
    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """
        获取账户摘要
        
        Args:
            account_id: 账户ID
            
        Returns:
            账户摘要信息
        """
        if account_id not in self.accounts:
            logger.error(f"账户不存在: {account_id}")
            return {}
        
        account = self.accounts[account_id]
        
        # 计算总资产
        total_assets = account.current_capital
        unrealized_pnl = 0.0
        
        for symbol, position in account.positions.items():
            # 获取当前价格
            current_price = await self._get_current_price(symbol)
            position.current_price = current_price
            
            # 计算未实现盈亏
            position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
            unrealized_pnl += position.unrealized_pnl
            
            # 计算仓位价值
            position_value = current_price * position.quantity
            total_assets += position_value
        
        # 计算绩效指标
        performance = await self._calculate_performance_metrics(account)
        
        summary = {
            "account_id": account_id,
            "broker_type": account.broker_type.value,
            "initial_capital": account.initial_capital,
            "current_capital": account.current_capital,
            "total_assets": total_assets,
            "unrealized_pnl": unrealized_pnl,
            "realized_pnl": sum(p.realized_pnl for p in account.positions.values()),
            "positions_count": len(account.positions),
            "open_orders": len([o for o in account.orders.values() 
                              if o.status in ["PENDING", "PARTIAL"]]),
            "total_trades": len(account.trade_history),
            "performance_metrics": performance,
            "last_update": datetime.now().isoformat()
        }
        
        return summary
    
    async def _get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        # 这里应该从市场数据源获取实时价格
        # 目前返回模拟价格
        
        if symbol in self.market_data:
            return self.market_data[symbol].get("price", 100.0)
        
        # 模拟价格
        base_price = 100 + (hash(symbol) % 50)
        change = np.random.normal(0, 1)
        return max(0.01, base_price + change)
    
    async def _calculate_performance_metrics(self, account: Account) -> Dict[str, float]:
        """计算绩效指标"""
        if not account.trade_history:
            return {}
        
        # 计算总收益
        total_return = (account.current_capital - account.initial_capital) / account.initial_capital
        
        # 计算胜率
        winning_trades = 0
        total_trades = len(account.trade_history)
        
        for trade in account.trade_history:
            if trade.get("action") == "SELL":
                # 这里需要更复杂的盈亏计算
                winning_trades += 1  # 简化处理
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 计算夏普比率 (简化版)
        returns = []
        for i in range(1, len(account.trade_history)):
            prev_balance = account.trade_history[i-1].get("account_balance", account.initial_capital)
            curr_balance = account.trade_history[i].get("account_balance", account.current_capital)
            ret = (curr_balance - prev_balance) / prev_balance if prev_balance > 0 else 0
            returns.append(ret)
        
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # 计算最大回撤
        balances = [trade.get("account_balance", account.current_capital) 
                   for trade in account.trade_history]
        if balances:
            peak = balances[0]
            max_drawdown = 0
            
            for balance in balances:
                if balance > peak:
                    peak = balance
                drawdown = (peak - balance) / peak if peak > 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
        else:
            max_drawdown = 0
        
        return {
            "total_return": float(total_return),
            "win_rate": float(win_rate),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "total_trades": total_trades,
            "winning_trades": winning_trades
        }
    
    async def update_market_data(self, symbol: str, data: Dict[str, float]):
        """
        更新市场数据
        
        Args:
            symbol: 股票代码
            data: 市场数据
        """
        self.market_data[symbol] = data
        
        # 更新所有相关仓位的当前价格
        for account in self.accounts.values():
            if symbol in account.positions:
                account.positions[symbol].current_price = data.get("price", 0)
    
    async def run_risk_checks(self, account_id: str) -> List[str]:
        """
        运行风险检查
        
        Args:
            account_id: 账户ID
            
        Returns:
            风险警告列表
        """
        warnings = []
        
        if account_id not in self.accounts:
            return ["账户不存在"]
        
        account = self.accounts[account_id]
        
        # 检查资金使用率
        total_position_value = 0
        for position in account.positions.values():
            total_position_value += position.current_price * position.quantity
        
        position_ratio = total_position_value / account.current_capital if account.current_capital > 0 else 0
        
        if position_ratio > 0.8:  # 仓位超过80%
            warnings.append(f"仓位过高: {position_ratio:.1%}")
        
        # 检查单只股票集中度
        for symbol, position in account.positions.items():
            position_value = position.current_price * position.quantity
            concentration = position_value / (account.current_capital + total_position_value)
            
            if concentration > 0.3:  # 单只股票超过30%
                warnings.append(f"{symbol} 集中度过高: {concentration:.1%}")
        
        # 检查回撤
        performance = await self._calculate_performance_metrics(account)
        if performance.get("max_drawdown", 0) > 0.1:  # 回撤超过10%
            warnings.append(f"回撤过大: {performance['max_drawdown']:.1%}")
        
        return warnings
    
    async def generate_trade_report(self, account_id: str, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        生成交易报告
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # 获取账户信息
        account = self.accounts.get(account_id)
        if not account:
            return {"error": f"账户 {account_id} 不存在"}
        
        # 获取该时间段内的订单
        period_orders = [
            order for order in account.orders
            if start_date <= order.created_at <= end_date
        ]
        
        # 计算绩效指标
        performance = await self._calculate_performance_metrics(account)
        
        # 生成报告
        report = {
            "account_id": account_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "initial_balance": account.initial_balance,
                "current_balance": account.balance,
                "total_return": performance.get("total_return", 0),
                "sharpe_ratio": performance.get("sharpe_ratio", 0),
                "max_drawdown": performance.get("max_drawdown", 0),
                "win_rate": performance.get("win_rate", 0)
            },
            "orders": [
                {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "action": order.action,
                    "quantity": order.quantity,
                    "price": order.price,
                    "status": order.status,
                    "created_at": order.created_at.isoformat()
                }
                for order in period_orders
            ],
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_price": pos.avg_price,
                    "current_value": pos.current_value,
                    "unrealized_pnl": pos.unrealized_pnl
                }
                for pos in account.positions.values()
            ]
        }
        
        return report
        生成交易