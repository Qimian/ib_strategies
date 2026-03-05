import os

from ib_trading.tools.logs import reset_log_dir as ib_trading_reset_log_dir 

app_name = "ib_strategies"


DEFAULT_MARKET_DATA_FIELDS = ["symbol", "last_price", "bid_price", "ask_price", "volume"]


# ib_trading log dir

IB_LOGS_PATH = os.path.join(
    os.path.abspath(__file__).replace("\\", "/").replace("\\\\", "/").split(
        f"{app_name}/src/{app_name}")[0], "ib_logs")


logs_dir = {
    "ib_trading": os.path.join(IB_LOGS_PATH, "logs", "ib_trading"),
    "ib_strategies": os.path.join(IB_LOGS_PATH, "logs", "ib_strategies"),
    "realtime_market_data": os.path.join(IB_LOGS_PATH, "logs", "realtime_market_data"),  
    }


def make_log_dir():
    for path in logs_dir.values():
        if not os.path.exists(path):
            os.makedirs(path)

make_log_dir()
ib_trading_reset_log_dir(logs_dir["ib_trading"])

def reset_log_dir(**kwargs):
    
    global logs_dir
    logs_dir.update(kwargs)

    make_log_dir()
    ib_trading_reset_log_dir(logs_dir["ib_trading"])

# url for ib gateway

gateway_url = "http://localhost:6688"

def reset_url(url: str):
    global gateway_url
    gateway_url = url