
from ib_strategies.tools import settings
from ib_trading.ib.ib_gateway_client import IBGatewayClient
from ib_strategies.tools.logs import log, log_decorator
from ib_strategies.trading_server import log_category

client = None

@log_decorator(category=log_category)
def init_connection():
    global client
    client = IBGatewayClient(settings.gateway_url)


@log_decorator(category=log_category)
def get_client():
    global client
    if client is None:
        init_connection()
    return client