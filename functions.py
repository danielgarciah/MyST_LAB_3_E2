import pandas as pd
import MetaTrader5 as Mt5
from typing import Optional
from os import path

class log_meta():

    def __init__(self, path, login, password, server, start_date, end_date):
        self.path = path
        self.login = login
        self.password = password
        self.server = server
        self.start_date = start_date
        self.end_date = end_date

    def f_login(self):
        connection = Mt5.initialize(path=self.path,
                                    login=self.login,
                                    password=self.password,
                                    server=self.server)
        if connection:
            print("Si funciona")
        else:
            print(Mt5.last_error())
            Mt5.shutdown()
        return Mt5

    def account_info(self):
        return self.f_login().account_info()

    def get_historical_deals(self, save_name: Optional[str] = None):
        tuplas = self.f_login().history_deals_get(self.start_date, self.end_date)
        df = pd.DataFrame(tuplas, columns=tuplas[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['time_msc'] = pd.to_datetime(df['time'], unit='ms')
        if save_name:
            reportpath = path.abspath('ReportesDeals_MT5/') + "/"
            df.to_excel(reportpath + save_name + ".xlsx")
        return df
    
    def get_historical_orders(self, save_name2: Optional[str] = None):
        tuplas2 = self.f_login().history_orders_get(self.start_date, self.end_date)
        df2 = pd.DataFrame(tuplas2, columns=tuplas2[0]._asdict().keys())
        #df2['time'] = pd.to_datetime(df2['time'], unit='s')
        #df2['time_msc'] = pd.to_datetime(df2['time'], unit='ms')
        if save_name2:
            reportpath2 = path.abspath('ReportesOrders_MT5/') + "/"
            df2.to_excel(reportpath2 + save_name2 + ".xlsx")
        return df2

class load_excel():

    def __init__(self, file_name):
        self.file_name = file_name

    def get_historical_deals(self):
        reportpath = path.abspath('ReportesDeals_MT5/') + "/"
        return pd.read_excel(reportpath + self.file_name + ".xlsx")
    
    def get_historical_orders(self):
        reportpath2 = path.abspath('ReportesOrders_MT5/') + "/"
        return pd.read_excel(reportpath2 + self.file_name + ".xlsx")


class est_desc():

    def __init__(self):
        pass

    def get_historical(self):
        return load_excel().get_historical()

    def get_info(self):
        return self.get_historical().info()





