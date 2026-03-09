from typing import List, Union, Dict
import threading
import datetime as dt
import time
import os
import sqlite3

from ib_strategies.strategy_base import StrategyBase, DEFAULT_MARKET_DATA_FIELDS
from ib_strategies.logs import MyLog
from ib_trading_no_order.ib_subscriber import DATABASE_FILENAME as PUBLIC_DATABASE_FILENAME
from ib_trading.tools.sqlite_tools import SQLiteTable
from ib_trading.ib.mkt_data import python_type_to_sqlite_type

STRATEGY_DATABASE_FILENAME = "IBRealtimeMarketDataSta.db"

class StrategySubscriber(StrategyBase):
    def __init__(self):

        super().__init__()

        self.data_snapshot: Dict[str, Dict] = {}
        self.stop_update_realtime_data_event = threading.Event()
        self.update_realtime_data_thread = None

        self.real_data_source = None
        self.sqlite_conn_sub = None
        self.sqlite_cursor_sub = None
        self.sqlite_conn_sta = None
        self.sqlite_cursor_sta = None
        self.init_sqlite_database()
        self.sqlite_table_sta = {}

        if self.my_datasource is not None:
            if self.my_datasource not in ["public_subscriber", "my_ibgc"]:
                raise ValueError(f"my_datasource must be one of ['public_subscriber', 'my_ibgc'] or None")
        
    
    @MyLog.log_decorator()
    def init_sqlite_database(self):
        """Initialize SQLite database connection"""

        # strategy database
        db_path = os.path.join(self.realtime_database_path, STRATEGY_DATABASE_FILENAME)
        self.sqlite_conn_sta = sqlite3.connect(db_path, check_same_thread=False)
        self.sqlite_cursor_sta = self.sqlite_conn_sta.cursor()

        self.logger.log("INFO", f"Strategy database initialized at: {db_path}", tag=self.log_id)

        # subscriber database
        db_path = os.path.join(self.realtime_database_path, PUBLIC_DATABASE_FILENAME)
        if os.path.exists(db_path):
            self.sqlite_conn_sub = sqlite3.connect(db_path, check_same_thread=False)
            self.sqlite_cursor_sub = self.sqlite_conn_sub.cursor()
        else:
            self.logger.log("INFO", f"Subscriber database file not found: {db_path}", tag=self.log_id)

    @MyLog.log_decorator()
    def init_sqlite_table(self, date, conid, symbol, data):

        table_name = f"RD_{symbol}_{conid}_{date.strftime('%Y%m%d')}"

        if table_name in self.sqlite_table_sta:
            return self.sqlite_table_sta[table_name]
        else:
            # 检查表是否存在
            self.sqlite_cursor_sta.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """, (table_name,))
            table_exists = self.sqlite_cursor_sta.fetchone() is not None

            # 定义必需的列和它们的类型
            required_columns = {
                "my_time": dt.datetime,
                "symbol": str,
                "conid": int,
                "_updated": dt.datetime,
                "strategy_name": str
            }

            # 从 data 中提取列
            data_columns = {}
            for key, value in data.items():
                if key in required_columns:
                    continue
                data_columns[key] = type(value)

            # 合并所有列
            all_columns = {**required_columns, **data_columns}

            # 创建列名映射（原始列名 -> SQL列名）
            # 如果列名是数字开头，加 col_ 前缀
            column_mapping = {}
            for col_name in all_columns.keys():
                if isinstance(col_name, str) and col_name.isdigit():
                    sql_col_name = f"col_{col_name}"
                elif isinstance(col_name, str) and col_name and col_name[0].isdigit():
                    sql_col_name = f"col_{col_name}"
                else:
                    sql_col_name = col_name
                column_mapping[col_name] = sql_col_name

            # 构建列定义
            column_defs = []
            for col_name, col_type in all_columns.items():
                sql_col_name = column_mapping[col_name]
                if col_name == "my_time":
                    column_defs.append(f"{sql_col_name} TEXT DEFAULT (datetime('now'))")
                elif col_name == "_updated":
                    column_defs.append(f"{sql_col_name} TEXT")
                else:
                    python_types = {str: "TEXT", int: "INTEGER", float: "REAL", dt.datetime: "TEXT", dt.date: "TEXT"}
                    sql_type = python_types.get(col_type, "TEXT")
                    column_defs.append(f"{sql_col_name} {sql_type}")

            # 添加复合主键：strategy_name 和 _updated
            if "_updated" in data:
                column_defs.append("PRIMARY KEY (strategy_name, _updated)")

            if not table_exists:
                # 创建表
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
                self.sqlite_cursor_sta.execute(create_sql)
                self.sqlite_conn_sta.commit()

                # 为 my_time 创建索引
                index_sql = f"CREATE INDEX IF NOT EXISTS idx_{table_name}_my_time ON {table_name}(my_time)"
                self.sqlite_cursor_sta.execute(index_sql)
                self.sqlite_conn_sta.commit()

                self.logger.log("INFO", f"Created table {table_name} with composite key (strategy_name, _updated)", tag=self.log_id)

            else:
                # 表已存在，检查并更新列
                self.sqlite_cursor_sta.execute(f"PRAGMA table_info({table_name})")
                existing_columns = {row[1]: row[2] for row in self.sqlite_cursor_sta.fetchall()}

                # 检查是否有缺少的列
                for col_name, col_type in all_columns.items():
                    sql_col_name = column_mapping[col_name]
                    if sql_col_name not in existing_columns:
                        if col_name == "my_time":
                            continue  # my_time 已由 DEFAULT 处理
                        sql_type = python_type_to_sqlite_type(col_type)
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {sql_col_name} {sql_type}"
                        try:
                            self.sqlite_cursor_sta.execute(alter_sql)
                            self.sqlite_conn_sta.commit()
                            self.logger.log("INFO", f"Added column {col_name} (sql_col_name: {sql_col_name}) to table {table_name}", tag=self.log_id)
                        except Exception as e:
                            self.logger.log("ERROR", f"Failed to add column {col_name}: {e}", tag=self.log_id)

            # 创建 SQLiteTable 对象，传递列名映射
            sqlite_table = SQLiteTable(self.sqlite_conn_sta, table_name, all_columns, column_mapping)
            self.sqlite_table_sta[table_name] = sqlite_table

            return sqlite_table



    def check_public_subscriber_datasource(self):
        """Check if public subscriber datasource is valid"""

        if self.sqlite_conn_sub is None:
            self.logger.log("INFO", f"cannot use public_subscriber: Cannot find public subscriber database", tag=self.log_id)
            return False

        today_str = dt.date.today().strftime('%Y%m%d')

        self.sqlite_cursor_sub.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in self.sqlite_cursor_sub.fetchall()]

        # 存储 conid 到表名的映射
        self.conid_to_table_name = {}
        # 存储 conid 到列名的映射
        self.conid_to_columns = {}

        # 为每个conid进行检查
        for conid in self.my_sub_conid:
            table_name = None
            for table in all_tables:
                # 表格名格式: RD_{symbol}_{conid}_{date}
                parts = table.split('_')
                if len(parts) >= 4:
                    table_conid = parts[2]
                    table_date = parts[3]
                    if table_conid == str(conid) and table_date == today_str:
                        table_name = table
                        break

            if table_name is None:
                self.logger.log("INFO", f"cannot use public_subscriber: No table found for conid {conid} on {today_str}", tag=self.log_id)
                return False

            # 记录 conid 到表名的映射
            self.conid_to_table_name[conid] = table_name

            # 获取并记录列信息
            self.sqlite_cursor_sub.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [row[1] for row in self.sqlite_cursor_sub.fetchall()]
            self.conid_to_columns[conid] = existing_columns

            # 检查字段是否覆盖 self.my_sub_fields
            for field in self.my_sub_fields:
                if field not in existing_columns:
                    self.logger.log("INFO", f"cannot use public_subscriber: Field {field} not found in table {table_name}", tag=self.log_id)
                    return False

            # 检查最新的my_time
            self.sqlite_cursor_sub.execute(f"SELECT MAX(my_time) FROM {table_name}")
            result = self.sqlite_cursor_sub.fetchone()

            if result and result[0]:
                latest_time_str = result[0]
                try:
                    latest_time = dt.datetime.fromisoformat(latest_time_str)
                    time_diff = (dt.datetime.now() - latest_time).total_seconds()

                    if time_diff > (self.realtime_data_interval*2):
                        self.logger.log("INFO", f"cannot use public_subscriber: Latest my_time is too old: {time_diff}s > {self.realtime_data_interval + 3}s for conid {conid}", tag=self.log_id)
                        return False
                except Exception as e:
                    self.logger.log("INFO", f"cannot use public_subscriber: Failed to parse my_time {latest_time_str} for conid {conid}: {e}", tag=self.log_id)
                    return False
            else:
                self.logger.log("INFO", f"cannot use public_subscriber: No my_time found in table {table_name} for conid {conid}", tag=self.log_id)
                return False

        self.logger.log("INFO", "can use public_subscriber: All public subscriber datasource checks passed", tag=self.log_id)
        return True


    @MyLog.log_decorator()
    def sub_ibgc_market_snapshot(self):

        self.ibgc.set_sub_fields(self.my_sub_fields)    
        self.ibgc.sub_market_snapshot(self.my_sub_conid)
    

    def add_realtime_market_data(self, t_conid, t_symbol, data):

        if self.real_data_source == "public_subscriber":
            return

        today = data["_updated"].date() if "_updated" in data else dt.date.today()
        table_name = f"RD_{t_symbol}_{t_conid}_{today.strftime('%Y%m%d')}"

        if table_name in self.sqlite_table_sta:
            sqlite_table =  self.sqlite_table_sta[table_name]
        else:
            sqlite_table = self.init_sqlite_table(today, t_conid, t_symbol, data)

        data["strategy_name"] = self.strategy_name
        if "_updated" in sqlite_table.columns and "_updated" in data:
            sqlite_table.upsert(data)
        else:
            sqlite_table.insert(data)



    def data_income(self, data):
        pass

    def _data_income(self, data):

        try:
            self.data_income(data)
        except Exception as e:
            self.logger.log("ERROR", f"data_income error: {e}, data:{data}", tag=self.log_id)

        
    @MyLog.log_decorator()
    def start_update_market_snapshot(self):
        if self.update_realtime_data_thread and self.update_realtime_data_thread.is_alive():
            self.logger.log("INFO", "Update market snapshot thread is already running", tag=self.log_id)
            return

        self.sub_date = None

        def update_func():

            self.stop_update_realtime_data_event.clear()

            while not self.stop_update_realtime_data_event.is_set():

                if dt.date.today()!=self.sub_date:
                    can_use_public = self.check_public_subscriber_datasource()
                    if not can_use_public:
                        self.real_data_source = "my_ibgc"
                    elif self.my_datasource is None:
                        self.real_data_source = "public_subscriber"
                    else:
                        self.real_data_source = self.my_datasource
                    self.sub_date = dt.date.today()

                    if self.real_data_source == "my_ibgc":
                        self.sub_ibgc_market_snapshot()

                    self.logger.log("INFO", f"Initial data source: {self.real_data_source}", tag=self.log_id)


                try:
                    if self.real_data_source == "my_ibgc":
    
                        t_snapshot = self.ibgc.get_market_snapshot()
                        for sp in t_snapshot:
                            t_conid, t_symbol = sp["conid"], sp["symbol"]
                            self.data_snapshot[f"{t_conid}_{t_symbol}"] = sp
                            self.data_snapshot[f"{t_conid}_{t_symbol}"]["my_time"] = dt.datetime.now()
                            self.add_realtime_market_data(t_conid, t_symbol, sp)
                            self._data_income(sp)
                    
                    elif self.real_data_source == "public_subscriber":
                        

                        for conid in self.my_sub_conid:
                            if self.real_data_source == "public_subscriber":
                                table_name = self.conid_to_table_name.get(conid)
                                self.sqlite_cursor_sub.execute(
                                    f"SELECT * FROM {table_name} ORDER BY my_time DESC LIMIT 1")
                                row = self.sqlite_cursor_sub.fetchone()
                                columns = self.conid_to_columns.get(conid, [])
                                data = dict(zip(columns, row))
                                
                                # check time diff = now - last subscriber data time
                                if data["my_time"]:
                                    try:
                                        time_diff = (dt.datetime.now() - dt.datetime.fromisoformat(data["my_time"])).total_seconds()
                                        if time_diff > self.realtime_data_interval * 2:
                                            raise Exception(f"Public subscriber data too old ({time_diff}s)")
                                    except Exception as e:
                                        self.logger.log("WARNING", f"Conid {conid} switching to my_ibgc for error: {e}", tag=self.log_id)
                                        self.real_data_source = "my_ibgc"
                                        self.sub_ibgc_market_snapshot()
                                        continue

                                self.data_snapshot[f"{conid}_{data['symbol']}"] = data
                                self.add_realtime_market_data(conid, data["symbol"], data)

                                self._data_income(data)


                except Exception as e:
                    print(e)
                    self.logger.log("WARNING", f"Failed to update snapshot: {e}", tag=self.log_id)
                self.stop_update_realtime_data_event.wait(self.realtime_data_interval)



        self.update_realtime_data_thread = threading.Thread(target=update_func, daemon=True)
        self.update_realtime_data_thread.start()
        self.logger.log("INFO", "Market snapshot update thread started", tag=self.log_id)

    @MyLog.log_decorator()
    def stop_update_market_snapshot(self):
        """Stop the market snapshot update thread"""
        if not self.update_realtime_data_thread or not self.update_realtime_data_thread.is_alive():
            self.logger.log("INFO", "Update market snapshot thread is not running", tag=self.log_id)
            return

        self.stop_update_realtime_data_event.set()
        self.logger.log("INFO", "Market snapshot update thread stop requested", tag=self.log_id)


    def __del__(self):

        self.stop_update_market_snapshot()
        super().__del__()
