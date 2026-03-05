import time

from ib_strategies.trading_server.connection import init_connection
from ib_strategies.trading_server.realtime_data import sub_market_snapshot, start_update_market_snapshot
from ib_trading.tools.logs import configure_httpx_logger

# Configure httpx logger to output to log file
configure_httpx_logger(category="httpx", level="DEBUG")

init_connection()

sub_market_snapshot([265598,4815747])
start_update_market_snapshot()


while True:
    time.sleep(60)