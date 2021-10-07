import pandas as pd
import MetaTrader5 as Mt5


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

    def get_historical(self):
        tuplas = self.f_login().history_deals_get(self.start_date, self.end_date)
        df = pd.DataFrame(tuplas, columns=tuplas[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['time_msc'] = pd.to_datetime(df['time'], unit='ms')
        return df
