
from ib_strategies.strategy_subscriber import StrategySubscriber
from ib_strategies.strategy_order import StrategyOrder
from ib_strategies.strategy_base import DEFAULT_GATEWAY_URL, DEFAULT_MARKET_DATA_FIELDS


class Strategy(StrategySubscriber, StrategyOrder):
    def __init__(self, 
                 strategy_name, 
                 account_id,
                 realtime_database_path,
                 gateway_url: str = DEFAULT_GATEWAY_URL,
                 log_dir = None,
                 schedule_task_interval = 10,
                 realtime_data_interval = 10,
                 my_datasource = None,
                 my_sub_fields = DEFAULT_MARKET_DATA_FIELDS,
                 my_sub_conid = [],
                 ):
        
        self._strategy_name = strategy_name
        self._account_id = account_id
        self._gateway_url = gateway_url
        self._log_dir = log_dir
        self._schedule_task_interval = schedule_task_interval
        self._realtime_data_interval = realtime_data_interval
        self._realtime_database_path = realtime_database_path
        self._my_datasource = my_datasource
        self._my_sub_fields = my_sub_fields
        self._my_sub_conid = my_sub_conid

        # Initialize all parent classes
        super().__init__()


    def data_income(self, data):
        pass

    def schedule_task(self):
        pass