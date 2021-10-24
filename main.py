from functions import log_meta, load_excel, est_desc, metricas_ad, behavioral_finance, visualizaciones
from datetime import datetime


usuario = 'Chelsi Sedano'
meta_path = 'C:\Program Files\MetaTrader 5 Terminal\\terminal64.exe'
login_count = 5400342 #'Bruno': 5400338 #'Chelsi': 5400342 #'Daniel': 5400339
password_count = 'XN1xho9d' #'Bruno': 'LHFFV4Nh' #'Chelsi': 'XN1xho9d' #'Daniel': '2qeDQrhu'
server_name = 'FxPro-MT5'
start_date = datetime(2021, 8, 1)
end_date = datetime.today()

log = log_meta(meta_path, login_count, password_count, server_name, start_date, end_date)
dat = load_excel(usuario)
est = est_desc(usuario)
metric = metricas_ad(usuario)
bf = behavioral_finance(meta_path, login_count, password_count, server_name)
vis = visualizaciones(usuario, meta_path, login_count, password_count, server_name)

if __name__ == "__main__":
    print(dat.historical())
    print(est.get_estadisticaba())
    print(metric.f_evolucion_capital())
    print(metric.f_estadisticas_mad())
    print(bf.f_be_de())
    print(vis.grafica_ranking())
    print(vis.grafica_draw())
    print(vis.grafica_disposicion())

