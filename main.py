from functions import log_meta, load_excel
from datetime import datetime


meta_path = 'C:\Program Files\MetaTrader 5 Terminal\\terminal64.exe'
login_count = 5400339 #'Bruno': 5400338 #'Chelsi': 5400342 #'Daniel': 5400339
pasword_count = '2qeDQrhu' #'Bruno': LHFFV4Nh' #'Chelsi': 'XN1xho9d' #'Daniel': '2qeDQrhu'
server_name = 'FxPro-MT5'
start_date = datetime(2021, 8, 1)
end_date = datetime.today()

log = log_meta(meta_path, login_count, pasword_count, server_name, start_date, end_date)
dat = load_excel('Historico_Chelsi')

if __name__ == "__main__":
    #print("Hello_World")
    #print(log.f_login())
    #print(log.account_info())
    #print(log.get_historical("prueba"))
    print(dat.get_historical())


