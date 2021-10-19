import pandas as pd
import numpy as np
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
        df2['time_setup'] = pd.to_datetime(df2['time_setup'], unit='s')
        df2['time_setup_msc'] = pd.to_datetime(df2['time_setup_msc'], unit='ms')
        if save_name2:
            reportpath2 = path.abspath('ReportesOrders_MT5/') + "/"
            df2.to_excel(reportpath2 + save_name2 + ".xlsx")
        return df2

    def get_total_historical(self):
        deals = self.get_historical_deals()
        order = self.get_historical_orders()

        deals['comment']= deals['comment'].fillna('No')
        deals['sl']=np.where(deals['comment'].str.contains('sl'),deals['comment'],'No')
        deals['sl']= deals.sl.str.extract('(\d+\.\d+)')
        deals['tp']=np.where(deals['comment'].str.contains('tp'),deals['comment'],'No')
        deals['tp']= deals.tp.str.extract('(\d+\.\d+)')
        
        deals = deals[['position_id', 'type', 'price', 'swap', 'profit', 'sl','tp']].copy()
        deals = deals[deals['position_id'] != 0]

        # Obtener la primera operacion
        operacion = deals.drop_duplicates(subset='position_id', keep='first', ignore_index=True)
        operacion = operacion.drop(columns=['swap', 'profit','sl','tp'])
        operacion['type'] = np.where(operacion['type'] == 0, 'buy', 'sell')

        # Obtener el precio al que se vendio o compro
        operacion2 = deals.drop_duplicates(subset='position_id', keep='last', ignore_index=True)
        operacion2 = operacion2.drop(columns='type')
        operacion2 = operacion2.rename(columns={'price': 'second_price','sl':'sl_op', 'tp': 'tp_op'})

        operacionT = pd.merge(operacion, operacion2, on='position_id')

        ordenes = order[['time_setup', 'symbol', 'position_id', 'type', 'volume_initial', 'sl', 'tp']].copy()

        ordenes1 = ordenes.drop_duplicates(subset='position_id', keep='first', ignore_index=True)
        ordenes1 = ordenes1.drop(columns='type')
        ordenes2 = ordenes.drop_duplicates(subset='position_id', keep='last', ignore_index=True)
        ordenes2 = ordenes2[['position_id', 'time_setup']]
        ordenes2 = ordenes2.rename(columns={'time_setup': 'time_setup2'})
        Operacion_Ordenes = pd.merge(operacionT, ordenes1, on='position_id')
        Operacion_Ordenes = pd.merge(Operacion_Ordenes, ordenes2, on='position_id')

        Operacion_Ordenes['sl_op']= Operacion_Ordenes['sl_op'].fillna('No')
        Operacion_Ordenes['tp_op']= Operacion_Ordenes['tp_op'].fillna('No')

        Operacion_Ordenes['sl_nuevo']=np.where((Operacion_Ordenes['sl']==0)&(Operacion_Ordenes['sl_op']!='No'),Operacion_Ordenes['sl_op'],Operacion_Ordenes['sl'])
        Operacion_Ordenes['tp_nuevo']=np.where((Operacion_Ordenes['tp']==0)&(Operacion_Ordenes['tp_op']!='No'),Operacion_Ordenes['tp_op'],Operacion_Ordenes['tp'])

        Operacion_Ordenes['sl_nuevo']=np.where((Operacion_Ordenes['sl']!=0)&(Operacion_Ordenes['sl_op']!='No')&(Operacion_Ordenes['sl']!= Operacion_Ordenes['sl_op']),Operacion_Ordenes['sl_op'],Operacion_Ordenes['sl_nuevo'])
        Operacion_Ordenes['tp_nuevo']=np.where((Operacion_Ordenes['tp']!=0)&(Operacion_Ordenes['tp_op']!='No')&(Operacion_Ordenes['tp']!= Operacion_Ordenes['tp_op']),Operacion_Ordenes['tp_op'],Operacion_Ordenes['tp_nuevo'])

        Operacion_Ordenes= Operacion_Ordenes[['position_id','symbol','type','time_setup','volume_initial','price','sl_nuevo','tp_nuevo','time_setup2','second_price','swap','profit']].copy()
        Operacion_Ordenes.rename(columns = {'sl_nuevo': 'sl','tp_nuevo':'tp'}, inplace = True)

        final = Operacion_Ordenes
        final['tiempo'] = final['time_setup2'] - final['time_setup']
        return final

    def pip_size(self, symbol: str):
        table = pd.read_csv("instruments_pips.csv")
        table["Instrument"] = table["Instrument"].str.replace("_", "")
        if symbol in list(table["Instrument"]):
            tick_table = list(table[table["Instrument"] == symbol].TickSize)[0]
        else:
            tick_table = 0.01
        pip_size = 1 / tick_table
        return pip_size

    def column_pip_size(self):
        historic = self.get_total_historical()
        symbols = historic['symbol']
        multiplicador = [self.pip_size(i) for i in symbols]
        historic['pip_size'] = multiplicador
        historic['pips'] = np.where(historic['type'] == "buy",
                                    (historic["second_price"] - historic["price"]) * historic["pip_size"],
                                    (historic["price"] - historic["second_price"]) * historic["pip_size"])
        historic['pips_acum'] = historic['pips'].cumsum()
        historic['profit_acum'] = historic['profit'].cumsum()
        #historic.to_excel("Historic_final_Daniel.xlsx")
        return historic

    def historical(self):
        df = self.column_pip_size()
        reportpath = path.abspath('Historicos/') + "/"
        save_name = self.account_info().name
        df.to_excel(reportpath + "Historic_final_" + save_name + ".xlsx")
        return df


class load_excel():

    def __init__(self, file_name_deals, file_name_orders, file_name_historical):
        self.file_name_deals = file_name_deals
        self.file_name_orders = file_name_orders
        self.file_name_historical = file_name_historical

    def get_historical_deals(self):
        report_path = path.abspath('ReportesDeals_MT5/') + "/"
        return pd.read_excel(report_path + self.file_name_deals + ".xlsx")
    
    def get_historical_orders(self):
        report_path2 = path.abspath('ReportesOrders_MT5/') + "/"
        return pd.read_excel(report_path2 + self.file_name_orders + ".xlsx")

    def get_total_historical(self):
        deals = self.get_historical_deals()
        order = self.get_historical_orders()

        deals['comment']= deals['comment'].fillna('No')
        deals['sl']=np.where(deals['comment'].str.contains('sl'),deals['comment'],'No')
        deals['sl']= deals.sl.str.extract('(\d+\.\d+)')
        deals['tp']=np.where(deals['comment'].str.contains('tp'),deals['comment'],'No')
        deals['tp']= deals.tp.str.extract('(\d+\.\d+)')
        
        deals = deals[['position_id', 'type', 'price', 'swap', 'profit', 'sl','tp']].copy()
        deals = deals[deals['position_id'] != 0]

        # Obtener la primera operacion
        operacion = deals.drop_duplicates(subset='position_id', keep='first', ignore_index=True)
        operacion = operacion.drop(columns=['swap', 'profit','sl','tp'])
        operacion['type'] = np.where(operacion['type'] == 0, 'buy', 'sell')

        # Obtener el precio al que se vendio o compro
        operacion2 = deals.drop_duplicates(subset='position_id', keep='last', ignore_index=True)
        operacion2 = operacion2.drop(columns='type')
        operacion2 = operacion2.rename(columns={'price': 'second_price','sl':'sl_op', 'tp': 'tp_op'})

        operacionT = pd.merge(operacion, operacion2, on='position_id')

        ordenes = order[['time_setup', 'symbol', 'position_id', 'type', 'volume_initial', 'sl', 'tp']].copy()

        ordenes1 = ordenes.drop_duplicates(subset='position_id', keep='first', ignore_index=True)
        ordenes1 = ordenes1.drop(columns='type')
        ordenes2 = ordenes.drop_duplicates(subset='position_id', keep='last', ignore_index=True)
        ordenes2 = ordenes2[['position_id', 'time_setup']]
        ordenes2 = ordenes2.rename(columns={'time_setup': 'time_setup2'})
        Operacion_Ordenes = pd.merge(operacionT, ordenes1, on='position_id')
        Operacion_Ordenes = pd.merge(Operacion_Ordenes, ordenes2, on='position_id')

        Operacion_Ordenes['sl_op'] = Operacion_Ordenes['sl_op'].fillna('No')
        Operacion_Ordenes['tp_op'] = Operacion_Ordenes['tp_op'].fillna('No')

        Operacion_Ordenes['sl_nuevo'] = np.where((Operacion_Ordenes['sl'] == 0) & (Operacion_Ordenes['sl_op'] != 'No'),
                                                  Operacion_Ordenes['sl_op'], Operacion_Ordenes['sl'])
        Operacion_Ordenes['tp_nuevo'] = np.where((Operacion_Ordenes['tp'] == 0) & (Operacion_Ordenes['tp_op'] != 'No'),
                                                  Operacion_Ordenes['tp_op'], Operacion_Ordenes['tp'])

        Operacion_Ordenes['sl_nuevo'] = np.where((Operacion_Ordenes['sl'] != 0) &
                                                 (Operacion_Ordenes['sl_op'] != 'No') &
                                                 (Operacion_Ordenes['sl'] != Operacion_Ordenes['sl_op']),
                                                 Operacion_Ordenes['sl_op'], Operacion_Ordenes['sl_nuevo'])
        Operacion_Ordenes['tp_nuevo'] = np.where((Operacion_Ordenes['tp'] != 0) &
                                                 (Operacion_Ordenes['tp_op'] != 'No') &
                                                 (Operacion_Ordenes['tp'] != Operacion_Ordenes['tp_op']),
                                                 Operacion_Ordenes['tp_op'],Operacion_Ordenes['tp_nuevo'])

        Operacion_Ordenes= Operacion_Ordenes[['position_id', 'symbol', 'type', 'time_setup', 'volume_initial',
                                              'price', 'sl_nuevo', 'tp_nuevo', 'time_setup2', 'second_price',
                                              'swap','profit']].copy()
        Operacion_Ordenes.rename(columns={'sl_nuevo': 'sl', 'tp_nuevo': 'tp'}, inplace=True)

        final = Operacion_Ordenes
        return final

    def historical(self):
        report_path = path.abspath('ReportesDeals_MT5/') + "/"
        return pd.read_excel(report_path + self.file_name_historical + ".xlsx")

class est_desc():

    def __init__(self):
        pass

    def get_historical(self):
        pass #return load_excel().get_historical()

    def get_info(self):
        pass # return self.get_historical().info()





