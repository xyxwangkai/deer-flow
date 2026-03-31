"""
纸面经纪商 - 用于模拟交易，不涉及真实资金
"""

from .simulation_broker import SimulationBroker, Account, Order, OrderType, OrderStatus
from typing import Dict, Any, Optional
import asyncio


class PaperBroker(SimulationBroker):
    """纸面经纪商 - 继承自模拟经纪商，添加更多模拟功能"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化纸面经纪商
        
        Args:
            config: 经纪商配置
        """
        super().__init__(config)
        self.slippage = config.get("slippage", 0.001)  # 滑点
        self.commission = config.get("commission", 0.0005)  # 佣金率
        self.market_impact = config.get("market_impact", 0.0001)  # 市场冲击
        
    async def place_order(self, account_id: str, symbol: str, side: str,
                         quantity: float, order_type: OrderType = OrderType.MARKET,
                         price: Optional[float] = None) -> Order:
        """
        下订单（纸面交易版本）
        
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
        order_id = f"PAPER_ORDER_{self.order_counter:06d}"
        
        # 创建订单
        order = Order(order_id, symbol, side, quantity, order_type, price)
        account.orders[order_id] = order
        
        # 模拟执行（纸面交易版本）
        await self._simulate_paper_execution(order, account)
        
        return order
    
    async def _simulate_paper_execution(self, order: Order, account: Account):
        """
        模拟纸面交易执行
        
        Args:
            order: 订单
            account: 账户
        """
        # 获取基准价格
        base_price = self._get_market_price(order.symbol)
        
        # 计算执行价格（考虑滑点、市场冲击）
        execution_price = self._calculate_execution_price(
            base_price, order.side, order.quantity, order.order_type, order.price
        )
        
        # 计算佣金
        commission_fee = self._calculate_commission(execution_price, order.quantity)
        
        if order.order_type == OrderType.MARKET:
            # 市价单立即执行
            order.filled_price = execution_price
            order.filled_quantity = order.quantity
            order.status = OrderStatus.FILLED
            order.filled_at = asyncio.get_event_loop().time()
            
            # 更新账户（考虑佣金）
            self._update_account_for_paper_order(order, account, execution_price, commission_fee)
            
        elif order.order_type == OrderType.LIMIT and order.price:
            # 限价单：如果执行价格优于限价，则执行
            if (order.side == "buy" and execution_price <= order.price) or \
               (order.side == "sell" and execution_price >= order.price):
                order.filled_price = execution_price
                order.filled_quantity = order.quantity
                order.status = OrderStatus.FILLED
                order.filled_at = asyncio.get_event_loop().time()
                
                # 更新账户（考虑佣金）
                self._update_account_for_paper_order(order, account, execution_price, commission_fee)
            else:
                # 价格未达到，保持挂单状态
                pass
        
        # 记录交易
        if order.status == OrderStatus.FILLED:
            transaction = {
                "transaction_id": f"PAPER_TRX_{len(account.transactions):06d}",
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "quantity": order.filled_quantity,
                "price": order.filled_price,
                "commission": commission_fee,
                "timestamp": order.filled_at,
                "account_id": account.account_id,
                "broker_type": "paper"
            }
            account.transactions.append(transaction)
    
    def _calculate_execution_price(self, base_price: float, side: str, 
                                  quantity: float, order_type: OrderType, 
                                  limit_price: Optional[float]) -> float:
        """
        计算执行价格
        
        Args:
            base_price: 基准价格
            side: 买卖方向
            quantity: 数量
            order_type: 订单类型
            limit_price: 限价（如果是限价单）
            
        Returns:
            执行价格
        """
        import random
        
        # 基础价格调整
        price = base_price
        
        # 考虑滑点
        slippage = random.uniform(-self.slippage, self.slippage)
        price *= (1 + slippage)
        
        # 考虑市场冲击（大订单会影响价格）
        impact_factor = min(quantity / 10000, 1.0)  # 假设10000股为基准
        market_impact = self.market_impact * impact_factor
        
        if side == "buy":
            # 买入会推高价格
            price *= (1 + market_impact)
        else:
            # 卖出会压低价格
            price *= (1 - market_impact)
        
        # 如果是限价单，确保价格不超过限价
        if order_type == OrderType.LIMIT and limit_price:
            if side == "buy":
                price = min(price, limit_price)
            else:
                price = max(price, limit_price)
        
        # 四舍五入到两位小数
        return round(price, 2)
    
    def _calculate_commission(self, price: float, quantity: float) -> float:
        """
        计算佣金
        
        Args:
            price: 价格
            quantity: 数量
            
        Returns:
            佣金费用
        """
        trade_value = price * quantity
        commission = trade_value * self.commission
        # 最低佣金
        min_commission = max(commission, 5.0)  # 最低5元
        return round(min_commission, 2)
    
    def _update_account_for_paper_order(self, order: Order, account: Account, 
                                       price: float, commission: float):
        """
        更新账户信息（纸面交易版本）
        
        Args:
            order: 订单
            account: 账户
            price: 成交价格
            commission: 佣金
        """
        total_cost = order.filled_quantity * price + commission
        
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
                # 卖出获得现金，扣除佣金
                account.cash += (order.filled_quantity * price - commission)
                account.positions[order.symbol] = current_position - order.filled_quantity
                
                # 如果持仓为0，删除该持仓记录
                if account.positions[order.symbol] == 0:
                    del account.positions[order.symbol]
            else:
                order.status = OrderStatus.REJECTED
                order.filled_quantity = 0
                order.filled_price = None
        
        account.last_updated = asyncio.get_event_loop().time()
    
    async def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """
        获取账户摘要（纸面交易版本）
        
        Args:
            account_id: 账户ID
            
        Returns:
            账户摘要信息
        """
        summary = await super().get_account_summary(account_id)
        
        # 添加纸面交易特定信息
        account = self.get_account(account_id)
        if account:
            # 计算总佣金
            total_commission = sum(
                t.get("commission", 0) for t in account.transactions 
                if isinstance(t, dict) and "commission" in t
            )
            
            summary.update({
                "broker_type": "paper",
                "slippage": self.slippage,
                "commission_rate": self.commission,
                "market_impact": self.market_impact,
                "total_commission": round(total_commission, 2),
                "simulation_features": True
            })
        
        return summary