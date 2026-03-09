import os
import time

from ib_strategies.strategy import Strategy


log_path = None
log_path_cans = [
    "/home/ib_work/ib_output",
    "/Users/xianqimian/GithubProjects/ib_output",
    ]
for p in log_path_cans:
    if os.path.exists(p):
        log_path = p
        break
if log_path is None:
    raise Exception("cannot find log path")




class MyStrategy(Strategy):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
    
    def data_income(self, data):

        print(self.my_datasource, self.real_data_source)
        print(data["symbol"], data["last_price"], data["_updated"]) 

        # print(self.preview_multiple_orders(
        #         [
        #             {
        #                 "conid": 265598,
        #                 "orderType": "LMT",
        #                 "side": "BUY",
        #                 "quantity": 1,
        #                 "price": 257.00,
        #                 "tif": "GTC"
        #             }
        #         ]
        #     ))

    def schedule_task(self):
        print("schedule task")


my_strategy = MyStrategy("test_strategy", 
                         account_id = "DUA507300",
                        realtime_database_path = os.path.join(log_path, "ib_data"),
                        gateway_url = "http://localhost:6688",
                        log_dir = os.path.join(log_path, "ib_logs/strategies"),
                        realtime_data_interval = 10,
                        schedule_task_interval = 10,
                        my_datasource = "public_subscriber",
                        my_sub_fields = ["symbol", "last_price", "bid_price", "ask_price", "volume"],
                        my_sub_conid = [265598,4815747,],
                        )

my_strategy.run_strategy()

