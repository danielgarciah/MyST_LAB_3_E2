import pandas as pd
import numpy as np
import statistics
import yfinance as yf
#import MetaTrader5 as Mt5
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
        report_path = path.abspath('Historicos/') + "/"
        return pd.read_excel(report_path + self.file_name_historical + ".xlsx")

class est_desc():
    
    def __init__(self, file_name_deals, file_name_orders, file_name_historical):
        self.file_name_deals = file_name_deals
        self.file_name_orders = file_name_orders
        self.file_name_historical = file_name_historical
        

    def get_historical(self):
        excel_lo=load_excel(self.file_name_deals,self.file_name_orders,self.file_name_historical)
        return excel_lo.historical()

    def get_estadisticaba(self):
        
        df = self.get_historical()
        
        ### df_1_tabla 
        Ops_totales= df['position_id'].count()
        Ganadoras= len(df[df['profit']>=0])
        Compras= df[df['type']=='buy']
        Ganadoras_c= len(Compras[Compras['profit']>=0])
        Ventas= df[df['type']=='sell']
        Ganadoras_v= len(Ventas[Ventas['profit']>=0])
        Perdedoras= len(df[df['profit']<0])
        Perdedoras_c= len(Compras[Compras['profit']<0])
        Perdedoras_v= len(Ventas[Ventas['profit']<0])
        Mediana_profit= df['profit'].median()
        Mediana_pips= df['pips'].median()
        r_efectividad= Ganadoras/Ops_totales
        r_proporcion=  Ganadoras/Perdedoras
        r_efectividad_c= Ganadoras_c/Ops_totales
        r_efectividad_v= Ganadoras_v/Ops_totales
        
        data_medidas = {'Medida':['Ops totales','Ganadoras','Ganadoras_c','Ganadoras_v','Perdedoras','Perdedoras_c','Perdedoras_v','Mediana (Profit)','Mediana (Pips)', 'r_efectividad','r_proporcion','r_efectividad_c','r_efectividad_v'],
       
        'Descripción':['Operaciones totales','Operaciones ganadoras','Operaciones ganadoras de compra','Operaciones ganadoras de venta',
                      'Operaciones perdedoras','Operaciones perdedoras de compra','Operaciones perdedoras de venta','Mediana de profit de operaciones','Mediana de pips de operaciones',
                      'Ganadoras Totales/Operaciones Totales','Ganadoras Totales/Perdedoras Totales','Ganadoras Compras/Operaciones Totales','Ganadoras Ventas/ Operaciones Totales'],
       
        'Valor':[Ops_totales,Ganadoras,Ganadoras_c,Ganadoras_v,Perdedoras,Perdedoras_c,Perdedoras_v,Mediana_profit,Mediana_pips,r_efectividad,r_proporcion,r_efectividad_c,r_efectividad_v]}

        df_1_tabla = pd.DataFrame(data_medidas)
        df_1_tabla['Valor']= df_1_tabla['Valor'].round(2)
        
        ### df_2_ranking

        df_2_ranking=pd.DataFrame(df.groupby(['symbol'])['symbol'].count())
        df_2_ranking= df_2_ranking.rename(columns = {'symbol': 'Total_symbols'})
        df_2_ranking= df_2_ranking.reset_index()

        Gan=df[df['profit']>0]
        Gan2=pd.DataFrame(Gan.groupby(['symbol'])['symbol'].count())
        Gan2= Gan2.rename(columns = {'symbol': 'Gan_symbols'})
        Gan2= Gan2.reset_index()

        df_2_ranking['Gan_symbols']= df_2_ranking['symbol'].map(Gan2.set_index('symbol')['Gan_symbols'])
        df_2_ranking['Gan_symbols']= df_2_ranking['Gan_symbols'].fillna(0)
        df_2_ranking['Gan_symbols'] = df_2_ranking['Gan_symbols'].astype(int)
        df_2_ranking['rank']= np.round((df_2_ranking['Gan_symbols']/df_2_ranking['Total_symbols'])*100,1)
        df_2_ranking['rank']= df_2_ranking['rank'].fillna(0)
        df_2_ranking.sort_values(by=['rank'],ascending=False, inplace=True,ignore_index=True)
        df_2_ranking['rank'] = df_2_ranking['rank'].astype(str) +'%'
        df_2_ranking= df_2_ranking.drop(columns= ['Total_symbols','Gan_symbols'])

        estadistica_ba = {}
        estadistica_ba["df_1_tabla"] = df_1_tabla
        estadistica_ba["df_2_ranking"] = df_2_ranking

        return estadistica_ba

class metricas_ad():

    def __init__(self, file_name_deals, file_name_orders, file_name_historical):
        self.file_name_deals = file_name_deals
        self.file_name_orders = file_name_orders
        self.file_name_historical = file_name_historical
        

    def get_historical(self):
        excel_lo=load_excel(self.file_name_deals,self.file_name_orders,self.file_name_historical)
        return excel_lo.historical()

    def f_evolucion_capital(self):
        df= self.get_historical()
        df['time_setup']= df['time_setup'].dt.date

        capital = 100000

        df2 = pd.DataFrame(df.groupby(['time_setup']).sum())
        idx = pd.date_range('2021-09-17', '2021-10-06')
        df2.index = pd.DatetimeIndex(df2.index)
        df2 = df2.reindex(idx, fill_value=0)

        data =pd.DataFrame()
        data['time'] = df2.index.unique()
        data['profit_d'] = np.array(df2['profit'])
        data['profit_acm_d'] = data['profit_d'] + capital
        i = 0
        n = len(data)-1
        data['profit_acm_d'] = data['profit_d'].cumsum() + capital

        return data

    def f_estadisticas_mad(self):
        data= self.f_evolucion_capital()
        df= self.get_historical()
        # Sharpe Ratio Original:
        rend = np.log(data.profit_acm_d) - np.log(data.profit_acm_d.shift(1))
        rend = rend.dropna()

        prom_rend_log = np.mean(rend)

        rf = .05

        des_est = statistics.pstdev(rend)

        Sharpe_O = (prom_rend_log-rf)/des_est

        # Descarga de precios standard and poor's 500
        fecha_inicial = df['time_setup'][0]
        fecha_final = df['time_setup'][len(df)-1]

        precios_sp500 = yf.download('^GSPC', start= fecha_inicial, end=fecha_final, interval='1d') 
        precios_sp500.drop(['Open', 'High', 'Low', 'Volume', 'Adj Close'], axis=1, inplace=True)
        precios_sp500['Date'] = precios_sp500.index

        # Sharpe Ratio Actualizado:
        rend_porta = np.log(data.profit_acm_d) - np.log(data.profit_acm_d.shift(1))
        rend_sp500 = np.log(precios_sp500.Close) - np.log(precios_sp500.Close.shift(1))

        rend_porta = rend_porta.dropna()
        rend_sp500 = rend_sp500.dropna()

        prom_rend_porta_log = np.mean(rend_porta)
        prom_rend_sp500_log = np.mean(rend_sp500)

        des_est = prom_rend_porta_log - prom_rend_sp500_log

        Sharpe_A = (prom_rend_porta_log - prom_rend_sp500_log)/des_est

        # DrawDown (Capital):

        posicion_min = data['profit_d'].idxmin()
        posicion_max = data[0:posicion_min+1]['profit_acm_d'].idxmax()

        data_min = data['profit_d'].min()
        data_max = data[0:posicion_min+1]['profit_acm_d'].max()

        fecha_inicial_dd = data['time'][posicion_max]
        fecha_final_dd = data['time'][posicion_min]

        # Drown up 
        data_min_du = data['profit_d'].min()
        data_max_du = data['profit_d'].max()

        posicion_max = data['profit_d'].idxmax()
        posicion_min = data['profit_d'].idxmin()


        fecha_inicial_du = data['time'][posicion_min]
        fecha_final_du = data['time'][posicion_max]

        metricas = pd.DataFrame()
        metricas['metrica'] = ['sharpe_original', 'sharpe_actualizado', 'drawdown_capi', 'drawdown_capi', 
                                'drawdown_capi', 'drawup_capi', 'drawup_capi', 'drawup_capi']
        metricas[''] = ['Cantidad', 'Cantidad', 'Fecha Inicial', 'Fecha Final', 'DrawDown $ (capital)',
                            'Fecha Inicial', 'Fecha Final', 'DrawDown $ (capital)']
        metricas['Valor'] = [Sharpe_O, Sharpe_A, fecha_inicial_dd, fecha_final_dd, data_min, fecha_inicial_du,
                                fecha_final_du, data_max_du]

        return metricas