from functions import log_meta, load_excel, est_desc, metricas_ad
#from functions import load_excel, est_desc, metricas_ad
from datetime import datetime


meta_path = 'C:\Program Files\MetaTrader 5 Terminal\\terminal64.exe'
login_count = 5400339 #'Bruno': 5400338 #'Chelsi': 5400342 #'Daniel': 5400339
password_count = '2qeDQrhu' #'Bruno': 'LHFFV4Nh' #'Chelsi': 'XN1xho9d' #'Daniel': '2qeDQrhu'
server_name = 'FxPro-MT5'
start_date = datetime(2021, 8, 1)
end_date = datetime.today()

log = log_meta(meta_path, login_count, password_count, server_name, start_date, end_date)
dat = load_excel('Historico_Chelsi', 'Orders_Chelsi', 'Historic_final_Chelsi Sedano')
est = est_desc('Historico_Chelsi', 'Orders_Chelsi','Historic_final_Chelsi Sedano')
metric= metricas_ad('Historico_Bruno', 'Orders_Bruno','Historic_final_Bruno Pimentel')

if __name__ == "__main__":
    print(log.historical())
    print(est.get_estadisticaba())
    print(metric.f_evolucion_capital())
    print(metric.f_estadisticas_mad())



