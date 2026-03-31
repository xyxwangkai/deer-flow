"""
模拟经纪商 - 用于回测和模拟交易
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import random
from enum import Enum


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """订单类"""
    
    def __init__(self, order_id: str, symbol: str, side: str, 
                 quantity: float, order_type: OrderType = OrderType.MARKET,
                 price: Optional[float] = None):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side  # "buy" or "sell"
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.status = OrderStatus.PENDING
        self.created_at = datetime.now()
        self.filled_at: Optional[datetime] = None
        self.filled_price: Optional[float] = None
        self.filled_quantity: float = 0.0


class Account:
    """账户类"""
    
    def __init__(self, account_id: str, initial_capital: float = 100000):
        self.account_id = account_id
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}  # symbol -> quantity
        self.orders: Dict[str, Order] = {}
        self.transactions: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
    @property
    def total_value(self) -> float:
        """计算账户总价值"""
        # 这里需要市场价格来计算持仓价值
        # 为了简化，我们假设所有持仓价值为0
        return self.cash


class SimulationBroker:
    """模拟经纪商"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化模拟经纪商
        
        Args:
            config: 经纪商配置
        """
        self.config = config
        self.accounts: Dict[str, Account] = {}
        self.market_data: Dict[str, pd.DataFrame] = {}
        self.order_counter = 0
        
    def create_account(self, account_id: str, initial_capital: float = 100000) -> Account:
        """
        创建交易账户
        
        Args:
            account_id: 账户ID
            initial_capital: 初始资金
            
        Returns:
            账户对象
        """
        account = Account(account_id, initial_capital)
        self.accounts[account_id] = account
        return account
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """
        获取账户
        
        Args:
            account_id: 账户ID
            
        Returns:
            账户对象或None
        """
        return self.accounts.get(account_id)
    
    async def place_order(self, account_id: str, symbol: str, side: str,
                         quantity: float, order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None) -> Order:
        """
        下订单
        
        Args:
            account_id: 账户ID
            symbol: 股票代码
            side: 买卖方向（"buy"/"sell"）
            quantity: 数量
            order_type: 订单类型
            price: 价格（限价单需要）
            
        Returns:
            订单对象
        """
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"账户 {account_id} 不存在")
        
        # 生成订单ID
        self.order_counter += 1
        order_id = f"ORDER_{self.order_counter:06d}"
        
        # 创建订单
        order = Order(order_id, symbol, side, quantity, order_type, price)
        account.orders[order_id] = order
        
        # 模拟执行
        await self._simulate_order_execution(order, account)
        
        return order
    
    async def _simulate_order_execution(self, order: Order, account: Account):
        """
        模拟订单执行
        
        Args:
            order: 订单
            account: 账户
        """
        # 模拟市场价
        current_price = self._get_market_price(order.symbol)
        
        if order.order_type == OrderType.MARKET:
            # 市价单立即执行
            order.filled_price = current_price
            order.filled_quantity = order.quantity
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            
            # 更新账户
            self._update_account_for_order(order, account, current_price)
            
        elif order.order_type == OrderType.LIMIT and order.price:
            # 限价单：如果当前价格优于限价，则执行
            if (order.side == "buy" and current_price <= order.price) or \
               (order.side == "sell" and current_price >= order.price):
                order.filled_price = order.price
                order.filled_quantity = order.quantity
                order.status = OrderStatus.FILLED
                order.filled_at = datetime.now()
                
                # 更新账户
                self._update_account_for_order(order, account, order.price)
            else:
                # 价格未达到，保持挂单状态
                pass
        
        # 记录交易
        if order.status == OrderStatus.FILLED:
            transaction = {
                "transaction_id": f"TRX_{len(account.transactions):06d}",
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.filled_quantity,
                "price": order.filled_price,
                "timestamp": order.filled_at.isoformat(),
                "account_id": account.account_id
            }
            account.transactions.append(transaction)
    
    def _get_market_price(self, symbol: str) -> float:
        """
        获取市场价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            市场价格
        """
        # 模拟价格生成
        base_prices = {
            "AAPL": 180.0,
            "GOOGL": 150.0,
            "MSFT": 400.0,
            "AMZN": 180.0,
            "TSLA": 200.0,
            "000001.SZ": 12.5,
            "000002.SZ": 25.0,
            "600519.SH": 1600.0,
        }
        
        base_price = base_prices.get(symbol, 100.0)
        # 添加随机波动
        fluctuation = random.uniform(-0.02, 0.02)
        return base_price * (1 + fluctuation)
    
    def _update_account_for_order(self, order: Order, account: Account, price: float):
        """
        更新账户信息
        
        Args:
            order: 订单
            account: 账户
            price: 成交价格
        """
        total_cost = order.filled_quantity * price
        
        if order.side == "buy":
            # 买入：减少现金，增加持仓
            if account.cash >= total_cost:
                account.cash -= total_cost
                account.positions[order.symbol] = account.positions.get(order.symbol, 0.0) + order.filled_quantity
            else:
                order.status = OrderStatus.REJECTED
                order.filled_quantity = 0
                order.filled_price = None
                
        elif order.side == "sell":
            # 卖出：检查是否有足够持仓
            current_position = account.positions.get(order.symbol, 0.0)
            if current_position >= order.filled_quantity:
                account.cash += total_cost
                account.positions[order.symbol] = current_position - order.filled_quantity
                
                # 如果持仓为0，删除该持仓记录
                if account.positions[order.symbol] == 0:
                    del account.positions[order.symbol]
            else:
                order.status = OrderStatus.REJECTED
                order.filled_quantity = 0
                order.filled_price = None
        
        account.last_updated = datetime.now()
    
    async def cancel_order(self, account_id: str, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            account_id: 账户ID
            order_id: 订单ID
            
        Returns:
            是否取消成功
        """
        account = self.get_account(account_id)
        if not account:
            return False
        
        order = account.orders.get(order_id)
        if not order:
            return False
        
        # 只能取消挂单状态的订单
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            return True
        
        return False
    
    async def get_order_status(self, account_id: str, order_id: str) -> Optional[OrderStatus]:
        """
        获取订单状态
        
        Args:
            account_id: 账户ID
            order_id: 订单ID
            
        Returns:
            订单状态或None
        """
        account = self.get_account(account_id)
        if not account:
            return None
        
        order = account.orders.get(order_id)
        if not order:
            return None
        
        return order.status
    
    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """
        获取账户摘要
        
        Args:
            account_id: 账户ID
            
        Returns:
            账户摘要信息
        """
        account = self.get_account(account_id)
        if not account:
            return {}
        
        # 计算持仓价值
        positions_value = 0.0
        for symbol, quantity in account.positions.items():
            price = self._get_market_price(symbol)
            positions_value += quantity * price
        
        total_value = account.cash + positions_value
        
        return {
            "account_id": account.account_id,
            "cash": account.cash,
            "positions": account.positions.copy(),
            "positions_value": positions_value,
            "total_value": total_value,
            "open_orders": len([o for o in account.orders.values() 
                               if o.status == OrderStatus.PENDING]),
            "total_orders": len(account.orders),
            "total_transactions": len(account.transactions),
            "created_at": account.created_at.isoformat(),
            "last_updated": account.last_updated.isoformat()
        }
    
    async def validate_connection(self) -> bool:
        """
        验证连接
        
        Returns:
            是否连接成功
        """
        return True