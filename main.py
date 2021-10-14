from functions import log_meta, load_excel, est_desc
#from functions import load_excel
from datetime import datetime


meta_path = 'C:\Program Files\MetaTrader 5 Terminal\\terminal64.exe'
login_count = 5400342 #'Bruno': 5400338 #'Chelsi': 5400342 #'Daniel': 5400339
password_count = 'XN1xho9d' #'Bruno': 'LHFFV4Nh' #'Chelsi': 'XN1xho9d' #'Daniel': '5400339'
server_name = 'FxPro-MT5'
start_date = datetime(2021, 8, 1)
end_date = datetime.today()

log = log_meta(meta_path, login_count, password_count, server_name, start_date, end_date)
dat = load_excel('Historico_Chelsi', 'Orders_Chelsi')
est = est_desc()

if __name__ == "__main__":
    #print("Hello_World")
    #print(log.f_login())
    #print(log.account_info())
    #print(log.get_historical_deals())
    #print(log.get_historical_orders())
    #print(dat.get_historical_deals())
    #print(log.get_historical_orders())
    #print(log.get_total_historical())
    #print(dat.get_total_historical())
    #print(est.pip_size())
    #print(log.pip_size("EURUSD"))
    print(log.column_pip_size())




