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




what_to_do = [0, 1, 2, 3, 4, 5]
order_id = None




class MyStrategy(Strategy):
    def __init__(self, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
    
    def data_income(self, data):

        print(self.my_datasource, self.real_data_source)
        print(data["symbol"], data["last_price"], data["_updated"]) 
        

    def schedule_task(self):

        global order_id
        global what_to_do

        i = None
        if len(what_to_do)>0:
            i = what_to_do.pop(0)

       
        if i==0:
            # 预览订单，假设下单然后
            print(f"{'='*30}")
            print("return of preview_multiple_orders")
            print(self.preview_multiple_orders(
                    [
                        {
                            "conid": 265598,
                            "orderType": "LMT", # 限价单
                            "side": "BUY",
                            "quantity": 1,
                            "price": 257.00,
                            "tif": "GTC"
                        }
                    ]
                ))
        elif i==1:
            # 市价买
            print(f"{'='*30}")
            print("return of place_multiple_orders")
            return_ = self.place_multiple_orders(
                    [
                        {
                            "conid": 265598,         # 苹果公司的合约 ID
                            "secType": "STK",        # 股票类型
                            "orderType": "MARKET",   # 关键：设置为市价单
                            "side": "BUY",           # 买入
                            "quantity": 1,          # 数量
                            "tif": "GTC"             # 订单有效期 (Good 'Til Canceled)
                        }
                    ]
                )
            order_id = return_[0]["order_id"]
            print(return_)
        elif i==2:
            print(f"{'='*30}")
            print("return of get_order_status")
            print(self.get_order_status(order_id))
        elif i==3:
            print(f"{'='*30}")
            print("return of get_all_orders")
            print(self.get_all_orders())
        elif i==4:
            print(f"{'='*30}")
            print("return of get_positions")
            print(self.ibgc.get_positions(self.account_id))
        elif i==5:
            status = self.get_order_status(order_id)
            if status["status"] == "Filled":
                print(f"{'='*30}")
                print("buy success, sell it now")
                print("return of place_multiple_orders")
                self.place_multiple_orders(
                    [
                        {
                            "conid": 265598,         # 苹果公司的合约 ID
                            "secType": "STK",        # 股票类型
                            "orderType": "MARKET",   # 关键：设置为市价单
                            "side": "SELL",           # 买入
                            "quantity": 1,          # 数量
                            "tif": "GTC"             # 订单有效期 (Good 'Til Canceled)
                        }
                    ]
                )
            else:
                print(f"{'='*30}")
                print("buy failed, cancel it")
                print("return of cancel_order")
                print(self.cancel_order(order_id))

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

