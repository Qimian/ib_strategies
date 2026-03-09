import os
import time
import datetime as dt

from ib_trading.ib.ib_gateway_client import IBGatewayClient
from ib_strategies.logs import MyLog, IB_LOGS_PATH


DEFAULT_GATEWAY_URL = "http://localhost:6688"
DEFAULT_MARKET_DATA_FIELDS = ["symbol", "last_price", "bid_price", "ask_price", "volume"]


class StrategyBase():

    def __init__(self):

        strategy_name = getattr(self, "_strategy_name")
        account_id = getattr(self, "_account_id")
        gateway_url = getattr(self, "_gateway_url", DEFAULT_GATEWAY_URL)
        log_dir = getattr(self, "_log_dir")
        my_datasource = getattr(self, "_my_datasource", None)
        my_sub_fields = getattr(self, "_my_sub_fields", DEFAULT_MARKET_DATA_FIELDS)
        my_sub_conid = getattr(self, "_my_sub_conid", [])
        realtime_data_interval = getattr(self, "_realtime_data_interval", 10)
        schedule_task_interval = getattr(self, "_schedule_task_interval", 10)
        realtime_database_path = getattr(self, "_realtime_database_path")

        # make log doc 
        if log_dir is None :
            temp_log_dir = os.path.join(os.getcwd(), f"tmp_log_{dt.datetime.now().strftime('%Y%m%d%H%M%S')}")
            os.makedirs(temp_log_dir, exist_ok=True)
            log_dir = temp_log_dir

        self.strategy_name = strategy_name
        self.account_id = account_id
        self.log_id = strategy_name

        self.t_stra_log_path = os.path.join(log_dir, strategy_name)
        self.logger = MyLog(
                        "strategy_log",
                        os.path.join(self.t_stra_log_path, "strategy_log"),
                        keep_days=30)

        self.ibgc = IBGatewayClient(base_url=gateway_url,
                                    heartbeat_interval=60,
                                    timeout=30,
                                    gateway_log_dir=os.path.join(self.t_stra_log_path, "ib_gateway_client"),
                                    heartbeat_log_dir=os.path.join(self.t_stra_log_path, "ib_gateway_client"),
                                    order_log_dir=os.path.join(self.t_stra_log_path, "ib_gateway_client"),
                                    log_keep_days=7)
        
        # other parameters
        self.my_datasource = my_datasource
        self.my_sub_fields = my_sub_fields
        self.my_sub_conid = my_sub_conid
        self.realtime_data_interval = realtime_data_interval
        self.schedule_task_interval = schedule_task_interval
        self.realtime_database_path = realtime_database_path

        
        self.logger.log("INFO", f"Strategy {strategy_name} initialized", tag=self.log_id)

    
    def run_strategy(self):

        if len(self.my_sub_conid)>0:
            self.start_update_market_snapshot()

        while True:
            time.sleep(self.schedule_task_interval)
            try:
                self.schedule_task()
                self.logger.log("INFO", f"Schedule task finished", tag=self.log_id)
            except Exception as e:
                self.logger.log("ERROR", f"Error in schedule_task: {e}", tag=self.log_id)

