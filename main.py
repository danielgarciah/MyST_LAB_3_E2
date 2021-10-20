from functions import log_meta, load_excel, est_desc, metricas_ad
#from functions import load_excel, est_desc, metricas_ad
from datetime import datetime


meta_path = 'C:\Program Files\MetaTrader 5 Terminal\\terminal64.exe'
login_count = 5400338 #'Bruno': 5400338 #'Chelsi': 5400342 #'Daniel': 5400339
password_count = 'LHFFV4Nh' #'Bruno': 'LHFFV4Nh' #'Chelsi': 'XN1xho9d' #'Daniel': '2qeDQrhu'
server_name = 'FxPro-MT5'
start_date = datetime(2021, 8, 1)
end_date = datetime.today()

log = log_meta(meta_path, login_count, password_count, server_name, start_date, end_date)
dat = load_excel('Chelsi Sedano')
est = est_desc('Chelsi Sedano')
metric = metricas_ad('Chelsi Sedano')

if __name__ == "__main__":
    print(dat.historical())
    print(est.get_estadisticaba())
    print(metric.f_evolucion_capital())
    print(metric.f_estadisticas_mad())
