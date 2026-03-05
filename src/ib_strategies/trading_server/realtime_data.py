from typing import List, Union, Dict
import threading
import datetime as dt
import time
import os

from ib_strategies.trading_server.connection import get_client
from ib_strategies.tools.settings import DEFAULT_MARKET_DATA_FIELDS
from ib_strategies.tools.logs import log, log_decorator
from ib_strategies.trading_server import log_category
from ib_strategies.tools.settings import logs_dir

# Global cache for market snapshot data
data_snapshot: Dict[str, Dict] = {}

# Log category
realtime_log_category = "realtime_data"

@log_decorator(category=log_category)
def sub_market_snapshot(conid: List[int]|int, fields: List[str] = DEFAULT_MARKET_DATA_FIELDS):

    get_client().set_sub_fields(fields)    
    get_client().sub_market_snapshot(conid)

    return True

# @log_decorator(category=log_category)
# def check_subscriptions() -> bool:
#     pass

def add_realtime_market_data(t_conid, t_symbol, data):
    today = data["_updated"].date() if "_updated" in data else dt.date.today()
    with open(os.path.join(logs_dir["realtime_market_data"],
            f"{t_symbol}_{t_conid}_{today}.log"), "a", encoding="utf-8") as f:
        f.write(str(data)+"\n") 


@log_decorator(category=log_category)
def start_update_market_snapshot():
    
    def update_func():

        global data_snapshot

        while True:
            try:
                t_snapshot = get_client().get_market_snapshot()
                for sp in t_snapshot:
                    t_conid, t_symbol, t_updated = sp["conid"], sp["symbol"], sp["_updated"]
                    if t_conid not in data_snapshot or \
                        t_updated != data_snapshot[t_conid]['_updated']:
                        sp["my_time"] = dt.datetime.now()
                        data_snapshot[f"{t_conid}_{t_symbol}"] = sp
                        add_realtime_market_data(t_conid, t_symbol, sp)
            except Exception as e:
                log(log_category, "ERROR", f"Failed to update snapshot: {e}")
            time.sleep(10)
    
    threading.Thread(target=update_func).start()


# def get_market_snapshot(conid: Union[int, List[int]]) -> Union[Dict, Dict[int, Dict]]:
#     """
#     Get market snapshot from local cache or fetch from server

#     Args:
#         conid: Contract ID or list of contract IDs

#     Returns:
#         Dict or Dict[int, Dict]: Market data snapshot(s)
#     """
#     global data_snapshot

#     client = get_client()

#     # Handle single conid
#     if isinstance(conid, int):
#         # Check if subscribed
#         sub = next((s for s in now_subscriptions if s["conid"] == conid), None)

#         if sub:
#             # Fetch fresh data from server
#             try:
#                 result = client.get_market_snapshot(conid)
#                 if isinstance(result, list) and len(result) > 0:
#                     # Update local cache
#                     data_snapshot[conid] = result[0]
#                     return result[0]
#                 else:
#                     log(log_category, "WARNING", f"No data returned for conid {conid}")
#             except Exception as e:
#                 log(log_category, "ERROR", f"Failed to get snapshot for conid {conid}: {e}")

#         # Return from cache or empty dict
#         return data_snapshot.get(conid, {})

#     # Handle list of conids
#     elif isinstance(conid, list):
#         result = {}
#         for c in conid:
#             result[c] = get_market_snapshot(c)
#         return result

#     else:
#         log(log_category, "ERROR", f"Invalid conid type: {type(conid)}")
#         return {}


# def update_market_snapshot():
#     """
#     Update all subscribed market snapshots by fetching fresh data from server
#     This should be called periodically to keep data fresh

#     Returns:
#         Dict[int, Dict]: Updated snapshot data for all conids
#     """
#     global data_snapshot


#     client = get_client()
#     updated_data = {}

#     for sub in now_subscriptions:
#         conid = sub["conid"]

#         try:
#             # Fetch fresh data
#             result = client.get_market_snapshot(conid)

#             if isinstance(result, list) and len(result) > 0:
#                 # Update local cache
#                 data_snapshot[conid] = result[0]
#                 updated_data[conid] = result[0]
#                 log(log_category, "DEBUG", f"Updated snapshot for conid {conid}")
#             else:
#                 log(log_category, "WARNING", f"No data returned for conid {conid}")

#         except Exception as e:
#             log(log_category, "ERROR", f"Failed to update snapshot for conid {conid}: {e}")

#     log(log_category, "INFO", f"Updated {len(updated_data)} snapshots out of {len(now_subscriptions)} subscriptions")
#     return updated_data


# def unsub_market_snapshot(conid: int = None):
#     """
#     Unsubscribe from market data snapshot

#     Args:
#         conid: Contract ID to unsubscribe. If None, unsubscribe all

#     Returns:
#         Dict: Response from IB Gateway
#     """
#     global now_subscriptions, data_snapshot

#     client = get_client()

#     try:
#         result = client.unsub_market_snapshot(conid)

#         if conid is None:
#             # Unsubscribe all
#             log(log_category, "INFO", f"Unsubscribed from all {len(now_subscriptions)} subscriptions")
#             now_subscriptions.clear()
#             data_snapshot.clear()
#         else:
#             # Remove specific subscription
#             now_subscriptions = [s for s in now_subscriptions if s["conid"] != conid]
#             if conid in data_snapshot:
#                 del data_snapshot[conid]
#             log(log_category, "INFO", f"Unsubscribed from conid {conid}")

#         return result

#     except Exception as e:
#         log(log_category, "ERROR", f"Failed to unsubscribe: {e}")
#         raise


