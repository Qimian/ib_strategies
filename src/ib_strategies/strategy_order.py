from typing import List, Dict

from ib_strategies.strategy_base import StrategyBase
from ib_strategies.logs import MyLog

PLACE_ORDER_WITHOUT_MARKET_DATA_WARNING = 'You are submitting an order without market data. We strongly recommend against this as it may result in erroneous and unexpected trades.\nAre you sure you want to submit this order?'


class StrategyOrder(StrategyBase):
    def __init__(self):

        super().__init__()

    @MyLog.log_decorator()
    def place_multiple_orders(self, orders: List[Dict]):
        """Place multiple orders

        Args:
            orders: List of order objects
 
        Returns:
            Dict: Order response from IB Gateway
        """
        

        return_ =  self.ibgc.place_orders(self.account_id, orders)

        if isinstance(return_, list) and len(return_) > 0 and 'id' in return_[0]:
            reply_id = return_[0]['id']
            message = return_[0]['message']
            if len(message)==1 and message[0]==PLACE_ORDER_WITHOUT_MARKET_DATA_WARNING:
                return self.order_reply(reply_id, True)
        else:
            return return_
        
    @MyLog.log_decorator()
    def preview_multiple_orders(self, orders: List[Dict]):
        """Preview orders without actually submitting

        Args:
            orders: List of order objects

        Returns:
            Dict: Order response from IB Gateway
        """
        return self.ibgc.preview_orders(self.account_id, orders)

    @MyLog.log_decorator()
    def cancel_order(self, order_id: str):
        """Cancel an order

        Args:
            account_id: Account ID
            order_id: Order ID to cancel

        Returns:
            Dict: Cancellation result
        """
        return self.ibgc.cancel_order(self.account_id, order_id)

    @MyLog.log_decorator()
    def modify_order(self, order_id: str, order: Dict):
        """Modify an existing order

        Args:
            account_id: Account ID
            order_id: Order ID to modify
            order: Order modification object

        Returns:
            Dict: Modification result
        """
        return self.ibgc.modify_order(self.account_id, order_id, order)

    @MyLog.log_decorator()
    def get_order_status(self, order_id: str):
        """Get status of a specific order

        Args:
            order_id: Order ID

        Returns:
            Dict: Order status information
        """
        return self.ibgc.get_order_status(order_id)

    @MyLog.log_decorator()
    def get_all_orders(self, filters: str = None):
        """Get all orders with optional filters

        Args:
            filters: Comma-separated list of filters (inactive, pending_submit, pre_submitted,
                     submitted, filled, pending_cancel, cancelled, warn_state, sort_by_time)

        Returns:
            Dict: All orders matching filters
        """
        return self.ibgc.get_orders(filters)

    @MyLog.log_decorator()
    def order_cancelled(self) -> bool:
        """Check if an order is cancelled

        Args:
            order_id: Order ID

        Returns:
            bool: True if order is cancelled
        """
        order_status = self.get_order_status(self.order_id)
        return order_status.get("order_status") == "Cancelled"

    @MyLog.log_decorator()
    def order_reply(self, reply_id: str, confirmed: bool) -> Dict:
        """Reply to an order"""
        return self.ibgc.reply_order(reply_id, confirmed)