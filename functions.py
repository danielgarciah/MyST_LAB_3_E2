import pandas as pd
import numpy as np
import statistics
import plotly.graph_objects as go
import yfinance as yf
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
            pass
        else:
            print(Mt5.last_error())
            Mt5.shutdown()
        return Mt5

    def account_info(self):
        return self.f_login().account_info()

    def get_historical_deals(self):
        tuplas = self.f_login().history_deals_get(self.start_date, self.end_date)
        df = pd.DataFrame(tuplas, columns=tuplas[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['time_msc'] = pd.to_datetime(df['time'], unit='ms')

        reportpath = path.abspath('ReportesDeals_MT5/') + "/"
        save_name = self.account_info().name
        df.to_excel(reportpath + "Deals_" + save_name + ".xlsx")
        return df
    
    def get_historical_orders(self, save_name2: Optional[str] = None):
        tuplas2 = self.f_login().history_orders_get(self.start_date, self.end_date)
        df2 = pd.DataFrame(tuplas2, columns=tuplas2[0]._asdict().keys())
        df2['time_setup'] = pd.to_datetime(df2['time_setup'], unit='s')
        df2['time_setup_msc'] = pd.to_datetime(df2['time_setup_msc'], unit='ms')

        reportpath = path.abspath('ReportesOrders_MT5/') + "/"
        save_name = self.account_info().name
        df2.to_excel(reportpath + "Orders_" + save_name + ".xlsx")
        return df2

    def get_total_historical(self):
        deals = self.get_historical_deals()
        order = self.get_historical_orders()

        deals['comment']= deals['comment'].fillna('No')
        deals['sl'] = np.where(deals['comment'].str.contains('sl'), deals['comment'],'No')
        deals['sl'] = deals.sl.str.extract('(\d+\.\d+)')
        deals['tp'] = np.where(deals['comment'].str.contains('tp'), deals['comment'],'No')
        deals['tp'] = deals.tp.str.extract('(\d+\.\d+)')
        
        deals = deals[['position_id', 'type', 'price', 'swap', 'profit', 'sl', 'tp']].copy()
        deals = deals[deals['position_id'] != 0]

        # Obtener la primera operacion
        operacion = deals.drop_duplicates(subset='position_id', keep='first', ignore_index=True)
        operacion = operacion.drop(columns=['swap', 'profit', 'sl', 'tp'])
        operacion['type'] = np.where(operacion['type'] == 0, 'buy', 'sell')

        # Obtener el precio al que se vendio o compro
        operacion2 = deals.drop_duplicates(subset='position_id', keep='last', ignore_index=True)
        operacion2 = operacion2.drop(columns='type')
        operacion2 = operacion2.rename(columns={'price': 'second_price', 'sl': 'sl_op', 'tp': 'tp_op'})

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
                                                 Operacion_Ordenes['tp_op'], Operacion_Ordenes['tp_nuevo'])

        Operacion_Ordenes = Operacion_Ordenes[['position_id', 'symbol', 'type', 'time_setup', 'volume_initial',
                                               'price', 'sl_nuevo', 'tp_nuevo', 'time_setup2', 'second_price',
                                               'swap', 'profit']].copy()
        Operacion_Ordenes.rename(columns={'sl_nuevo': 'sl', 'tp_nuevo': 'tp'}, inplace=True)

        final = Operacion_Ordenes
        final['tiempo'] = final['time_setup2'] - final['time_setup']
        final = final.rename(columns={'time_setup': 'opentime', 'time_setup2': 'closetime'})
        final['tiempo'] = final['tiempo'].dt.total_seconds().astype("int")
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
        return historic

    def historical(self):
        df = self.column_pip_size()
        reportpath = path.abspath('Historicos/') + "/"
        save_name = self.account_info().name
        df.to_excel(reportpath + "Historic_final_" + save_name + ".xlsx")
        return df


class load_excel():

    def __init__(self, user_name: int):
        self.user_name = user_name

    def get_historical_deals(self):
        report_path = path.abspath('ReportesDeals_MT5/') + "/"
        return pd.read_excel(report_path + 'Deals_' + self.user_name + ".xlsx", index_col=0)
    
    def get_historical_orders(self):
        report_path2 = path.abspath('ReportesOrders_MT5/') + "/"
        return pd.read_excel(report_path2 + 'Orders_' + self.user_name + ".xlsx", index_col=0)

    def historical(self):
        report_path = path.abspath('Historicos/') + "/"
        return pd.read_excel(report_path + 'Historic_final_' + self.user_name + ".xlsx", index_col=0)


class est_desc():
    
    def __init__(self, user_name):
        self.user_name = user_name

    def get_historical(self):
        excel_lo = load_excel(self.user_name)
        return excel_lo.historical()

    def get_estadisticaba(self):
        df = self.get_historical()
        
        ### df_1_tabla 
        Ops_totales = df['position_id'].count()
        Ganadoras = len(df[df['profit'] >= 0])
        Compras = df[df['type'] == 'buy']
        Ganadoras_c = len(Compras[Compras['profit'] >= 0])
        Ventas = df[df['type'] == 'sell']
        Ganadoras_v = len(Ventas[Ventas['profit'] >= 0])
        Perdedoras = len(df[df['profit'] < 0])
        Perdedoras_c = len(Compras[Compras['profit'] < 0])
        Perdedoras_v = len(Ventas[Ventas['profit'] < 0])
        Mediana_profit = df['profit'].median()
        Mediana_pips = df['pips'].median()
        r_efectividad = Ganadoras/Ops_totales
        r_proporcion = Ganadoras/Perdedoras
        r_efectividad_c = Ganadoras_c/Ops_totales
        r_efectividad_v = Ganadoras_v/Ops_totales
        
        data_medidas = {'Medida': ['Ops totales', 'Ganadoras', 'Ganadoras_c', 'Ganadoras_v', 'Perdedoras',
                                   'Perdedoras_c', 'Perdedoras_v', 'Mediana (Profit)', 'Mediana (Pips)',
                                   'r_efectividad', 'r_proporcion', 'r_efectividad_c', 'r_efectividad_v'],
                        'Descripción': ['Operaciones totales', 'Operaciones ganadoras',
                                        'Operaciones ganadoras de compra', 'Operaciones ganadoras de venta',
                                        'Operaciones perdedoras', 'Operaciones perdedoras de compra',
                                        'Operaciones perdedoras de venta', 'Mediana de profit de operaciones',
                                        'Mediana de pips de operaciones', 'Ganadoras Totales/Operaciones Totales',
                                        'Ganadoras Totales/Perdedoras Totales', 'Ganadoras Compras/Operaciones Totales',
                                        'Ganadoras Ventas/ Operaciones Totales'],
                        'Valor': [Ops_totales, Ganadoras, Ganadoras_c, Ganadoras_v, Perdedoras, Perdedoras_c,
                                  Perdedoras_v, Mediana_profit, Mediana_pips, r_efectividad, r_proporcion,
                                  r_efectividad_c, r_efectividad_v]}

        df_1_tabla = pd.DataFrame(data_medidas)
        df_1_tabla['Valor'] = df_1_tabla['Valor'].round(2)
        
        ### df_2_ranking
        df_2_ranking = pd.DataFrame(df.groupby(['symbol'])['symbol'].count())
        df_2_ranking = df_2_ranking.rename(columns={'symbol': 'Total_symbols'})
        df_2_ranking = df_2_ranking.reset_index()

        Gan = df[df['profit'] > 0]
        Gan2 = pd.DataFrame(Gan.groupby(['symbol'])['symbol'].count())
        Gan2 = Gan2.rename(columns={'symbol': 'Gan_symbols'})
        Gan2 = Gan2.reset_index()

        df_2_ranking['Gan_symbols'] = df_2_ranking['symbol'].map(Gan2.set_index('symbol')['Gan_symbols'])
        df_2_ranking['Gan_symbols'] = df_2_ranking['Gan_symbols'].fillna(0)
        df_2_ranking['Gan_symbols'] = df_2_ranking['Gan_symbols'].astype(int)
        df_2_ranking['rank'] = np.round((df_2_ranking['Gan_symbols']/df_2_ranking['Total_symbols'])*100, 1)
        df_2_ranking['rank'] = df_2_ranking['rank'].fillna(0)
        df_2_ranking.sort_values(by=['rank'], ascending=False, inplace=True, ignore_index=True)
        df_2_ranking['rank'] = df_2_ranking['rank'].astype(str) + '%'
        df_2_ranking = df_2_ranking.drop(columns=['Total_symbols', 'Gan_symbols'])

        estadistica_ba = {}
        estadistica_ba["df_1_tabla"] = df_1_tabla
        estadistica_ba["df_2_ranking"] = df_2_ranking

        return estadistica_ba


class metricas_ad():

    def __init__(self, user_name):
        self.user_name = user_name

    def get_historical(self):
        excel_lo = load_excel(self.user_name)
        return excel_lo.historical()

    def f_evolucion_capital(self):
        df = self.get_historical()
        df['opentime'] = df['opentime'].dt.date

        capital = 100000

        df2 = pd.DataFrame(df.groupby(['opentime']).sum())
        idx = pd.date_range('2021-09-17', '2021-10-06')
        df2.index = pd.DatetimeIndex(df2.index)
        df2 = df2.reindex(idx, fill_value=0)

        data = pd.DataFrame()
        data['time'] = df2.index.unique()
        data['profit_d'] = np.array(df2['profit'])
        data['profit_acm_d'] = data['profit_d'] + capital
        i = 0
        n = len(data)-1
        data['profit_acm_d'] = data['profit_d'].cumsum() + capital
        return data

    def estadisticas_fig(self):
        data = self.f_evolucion_capital()
        df = self.get_historical()

        # Sharpe Ratio Original:
        rend = np.log(data.profit_acm_d) - np.log(data.profit_acm_d.shift(1))
        rend = rend.dropna()

        prom_rend_log = np.mean(rend)
        rf = .05
        des_est = statistics.pstdev(rend)
        Sharpe_O = (prom_rend_log-rf)/des_est

        # Descarga de precios standard and poor's 500
        fecha_inicial = df['opentime'][0]
        fecha_final = df['opentime'][len(df)-1]

        precios_sp500 = yf.download('^GSPC', start=fecha_inicial, end=fecha_final, interval='1d', progress=False)
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

        #

        data_min = data['profit_acm_d'].min()
        data_max = data['profit_acm_d'].max()

        posicion_max = data['profit_acm_d'].idxmax()
        posicion_min = data['profit_acm_d'].idxmin()

        fecha_max = data['time'][posicion_max]
        fecha_min = data['time'][posicion_min]

        if fecha_max > fecha_min:
            fecha_inicial_dd = data.loc[0, 'time']
            fecha_final_dd = fecha_min
            fecha_inicial_du = data['time'][posicion_min]
            fecha_final_du = fecha_max
        else:
            fecha_inicial_du = data.loc[0, 'time']
            fecha_final_du = fecha_max
            fecha_inicial_dd = data['time'][posicion_max]
            fecha_final_dd = fecha_min

        estadisticas = pd.DataFrame()
        estadisticas['metrica'] = ['sharpe_original', 'sharpe_actualizado', 'drawdown_capi', 'drawdown_capi',
                                   'drawdown_capi', 'drawup_capi', 'drawup_capi', 'drawup_capi']
        estadisticas[''] = ['Cantidad', 'Cantidad', 'Fecha Inicial', 'Fecha Final', 'DrawDown $ (capital)',
                            'Fecha Inicial', 'Fecha Final', 'DrawDown $ (capital)']
        estadisticas['Valor'] = [Sharpe_O, Sharpe_A, fecha_inicial_dd, fecha_final_dd, data_min, fecha_inicial_du,
                                 fecha_final_du, data_max]
        
        estadisticas['descripcion'] = ['Sharpe Ratio Fórmula Original', 'Sharpe Ratio Fórmula Ajustada' , 'Fecha inicial del DrawDown de Capital' , 
        'Fecha final del DrawDown de Capital', 'Máxima pérdida flotante registrada', 'Fecha inicial del DrawUp de Capital', 
        'Fecha final del DrawUp de Capital', 'Máxima ganancia flotante registrada']

        data.set_index('time', inplace=True)

        x_dd = data.loc[fecha_inicial_dd:fecha_final_dd].index
        y_dd = data.loc[fecha_inicial_dd:fecha_final_dd]['profit_acm_d']

        x_du = data.loc[fecha_inicial_du:fecha_final_du].index
        y_du = data.loc[fecha_inicial_du:fecha_final_du]['profit_acm_d']

        x_cc = data.index
        y_cc = data['profit_acm_d']

        fig = go.Figure()

        fig.add_trace(go.Scatter(x=x_cc, y=y_cc, name='Profit diario', mode='lines', line=dict(color='black')))
        fig.add_trace(go.Scatter(x=x_dd, y=y_dd, name='Drawdown', mode='lines',
                                 line=dict(color='red', width=4, dash='dashdot')))
        fig.add_trace(go.Scatter(x=x_du, y=y_du, name='Drawdup', mode='lines',
                                 line=dict(color='Green', width=4, dash='dashdot')))

        return estadisticas, fig

    def f_estadisticas_mad(self):
        estadisticas, fig = self.estadisticas_fig()
        return estadisticas


class behavioral_finance():

    def __init__(self, path, login, password, server):
        self.path = path
        self.login = login
        self.password = password
        self.server = server

    def dictionary_figure(self):
        connection = Mt5.initialize(path=self.path,
                                    login=self.login,
                                    password=self.password,
                                    server=self.server)

        user_name = Mt5.account_info().name

        excel_lo = load_excel(user_name)
        df = excel_lo.historical()

        df['ratio'] = round((df['profit'] / df['profit_acum']) * 100, 2)

        df_anclas = df[df['profit'] >= 0]

        id_gan = list()
        id_per = list()
        profit_gan = list()
        profit_per = list()
        profit_acum = list()
        ratio_per = list()
        ratio_gan = list()
        df_anclas = df_anclas.reset_index(drop=True)

        for i in range(1, len(df_anclas)):
            for j in range(1, len(df)):
                if df_anclas.loc[i, 'closetime'] >= df.loc[j, 'opentime'] and df_anclas.loc[i, 'closetime'] < df.loc[j, 'closetime']:
                    precio = Mt5.copy_ticks_from(df.loc[j, 'symbol'],
                                                 df_anclas.loc[i, 'closetime'],
                                                 1,
                                                 Mt5.TIMEFRAME_M5)

                    if df.loc[j, 'type'] == "buy":
                        precio_f = precio[0][1]
                        pip_nuevo = (precio_f - df.loc[j, 'second_price']) * df.loc[j, 'pip_size']
                    else:
                        precio_f = precio[0][2]
                        pip_nuevo = (df.loc[j, 'second_price'] - precio_f) * df.loc[j, 'pip_size']

                    profit_nuevo = (df.loc[j, 'profit'] / df.loc[j, 'pips']) * pip_nuevo
                    if profit_nuevo < 0:
                        id_gan.append(df_anclas.loc[i, 'position_id'])
                        id_per.append(df.loc[j, 'position_id'])
                        profit_gan.append(df_anclas.loc[i, 'profit'])
                        profit_per.append(profit_nuevo)
                        profit_acum.append(df_anclas.loc[i, 'profit_acum'])
                        ratio_gan.append(df_anclas.loc[i, 'ratio'])
                        ratio_per.append(df.loc[j, 'ratio'])

        potenciales = pd.DataFrame()
        potenciales['id_gan'] = id_gan
        potenciales['profit_gan'] = profit_gan
        potenciales['ratio_gan'] = ratio_gan
        potenciales['id_per'] = id_per
        potenciales['profit_per'] = profit_per
        potenciales['ratio_per'] = ratio_per
        potenciales['profit_acum'] = profit_acum

        potenciales_finales = potenciales.groupby(['id_gan']).max(["profit_per"])

        ocurrencias = len(potenciales_finales)
        dictionary = {'Ocurrencias': {
            'Cantidad': ocurrencias}}

        status = 0
        aversion = 0
        sensibilidad = 0
        for i in range(len(potenciales_finales)):
            if potenciales_finales.iloc[i, 3] / potenciales_finales.iloc[i, 5] < \
                    potenciales_finales.iloc[i, 0] / potenciales_finales.iloc[i, 5]:
                status += 1
            if abs(potenciales_finales.iloc[i, 3] / potenciales_finales.iloc[i, 0]) > 2:
                aversion += 1

        if potenciales_finales.iloc[-1, 5] > potenciales_finales.iloc[0, 5]:
            sensibilidad += 1
        if potenciales_finales.iloc[-1, 0] > potenciales_finales.iloc[0, 0] and \
                potenciales_finales.iloc[-1, 3] > potenciales_finales.iloc[0, 3]:
            sensibilidad += 1
        if potenciales_finales.iloc[-1, 3] / potenciales_finales.iloc[-1, 0] > 2:
            sensibilidad += 1

        status_quo = str(round((status / ocurrencias) * 100, 2)) + "%"
        aversion_perdida = str(round((aversion / ocurrencias) * 100, 2)) + "%"
        if sensibilidad >= 2:
            sensibilidad_decreciente = "Si"
        else:
            sensibilidad_decreciente = "No"
        bf = pd.DataFrame(data=np.array([[ocurrencias, status_quo, aversion_perdida, sensibilidad_decreciente]]),
                          columns=['ocurrencias',
                                   'status_quo',
                                   'aversion_perdida',
                                   'sensibilidad_decreciente'])

        for i in range(ocurrencias):
            dictionary["Ocurrencia_" + str(i + 1)] = {'timestamp': str(list(df_anclas[df_anclas['position_id'] == \
                                                                                      potenciales_finales.index[i]][
                                                                                'opentime'])[0]),
                                                      'Operaciones': {
                                                          'Ganadora': {
                                                              'Instrumento': list(df_anclas[df_anclas['position_id'] == \
                                                                                            potenciales_finales.index[
                                                                                                i]]['symbol'])[0],
                                                              'Volumen': list(df_anclas[df_anclas['position_id'] == \
                                                                                        potenciales_finales.index[i]][
                                                                                  'volume_initial'])[0],
                                                              'Sentido': list(df_anclas[df_anclas['position_id'] == \
                                                                                        potenciales_finales.index[i]][
                                                                                  'type'])[0],
                                                              'Profit_ganadora':
                                                                  list(df_anclas[df_anclas['position_id'] == \
                                                                                 potenciales_finales.index[i]][
                                                                           'profit'])[0]
                                                          },
                                                          'Perdedora': {
                                                              'Instrumento': list(df[df['position_id'] == \
                                                                                     potenciales_finales.iloc[i, 2]][
                                                                                      'symbol'])[0],
                                                              'Volumen': list(df[df['position_id'] == \
                                                                                 potenciales_finales.iloc[i, 2]][
                                                                                  'volume_initial'])[0],
                                                              'Sentido': list(df[df['position_id'] == \
                                                                                 potenciales_finales.iloc[i, 2]][
                                                                                  'type'])[0],
                                                              'Profit_perdedora': np.round(
                                                                  potenciales_finales.iloc[i, 3], 2)
                                                          }
                                                      },
                                                      'Ratio_cp_profit_acm': np.round(
                                                          potenciales_finales.iloc[i, 3] / potenciales_finales.iloc[
                                                              i, 5], 2),
                                                      'Ratio_cg_profit_acm': np.round(
                                                          potenciales_finales.iloc[i, 0] / potenciales_finales.iloc[
                                                              i, 5], 2),
                                                      'Ratio_cp_cg': np.round(
                                                          potenciales_finales.iloc[i, 3] / potenciales_finales.iloc[
                                                              i, 0], 2)
                                                      }
        dictionary["Resultados"] = {'Dataframe': bf}

        sensi_decre = 0
        for i in range(1, len(potenciales_finales)):
            sensi = 0
            if potenciales_finales.iloc[i, 5] > potenciales_finales.iloc[i - 1, 5]:
                sensi += 1
            if potenciales_finales.iloc[i, 0] > potenciales_finales.iloc[i - 1, 0] and \
                    potenciales_finales.iloc[i, 3] > potenciales_finales.iloc[i - 1, 3]:
                sensi += 1
            if potenciales_finales.iloc[i, 3] / potenciales_finales.iloc[i, 0] > 2:
                sensi += 1
            if sensi >= 2:
                sensi_decre += 1

        bf_titles = ['status_quo', 'aversion_perdida', 'sensibilidad_decreciente']

        fig = go.Figure(data=[
            go.Bar(name='Si', x=bf_titles, y=[status, aversion, sensi_decre]),
            go.Bar(name='No', x=bf_titles,
                   y=[(ocurrencias - status), (ocurrencias - aversion), (ocurrencias - sensi_decre)])
        ])

        # Change the bar mode
        fig.update_layout(barmode='group')

        return dictionary, fig

    def f_be_de(self):
        dic, fig = self.dictionary_figure()
        return dic


class visualizaciones():

    def __init__(self, user_name, path, login, password, server):
        self.user_name = user_name
        self.path = path
        self.login = login
        self.password = password
        self.server = server

    def grafica_ranking(self):

        est = est_desc(self.user_name).get_estadisticaba()
        df_2_ranking = pd.DataFrame(est["df_2_ranking"])
        labels = df_2_ranking['symbol']
        values = list((df_2_ranking['rank'].str.replace("%", "")).astype(float))

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, pull=[0.1]+[0]*(len(df_2_ranking)-1), textinfo='label+ percent')])
        fig.update_layout(title_text='Gráfica 1: Ranking')
        fig.show()

    def grafica_draw(self):
        estadisticas, fig = metricas_ad(self.user_name).estadisticas_fig()
        fig.update_layout(title_text='Gráfica 2: DrawDown y DrawUp')
        fig.show()

    def grafica_disposicion(self):
        dic, fig = behavioral_finance(self.path, self.login, self.password, self.server).dictionary_figure()
        fig.update_layout(title_text='Gráfica 3: Disposition Effect')
        fig.show()
