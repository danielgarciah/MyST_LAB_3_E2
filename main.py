#from functions import log_meta
from functions import download_report
from datetime import datetime
from os import path


#meta_path = 'C:\Program Files\MetaTrader 5 Terminal\\terminal64.exe'
#login_count = 5400339
#pasword_count = '2qeDQrhu'
#server_name = 'FxPro-MT5'
#start_date = datetime(2021, 8, 1)
#end_date = datetime.today()

#log = log_meta(meta_path, login_count, pasword_count, server_name, start_date, end_date)

report_name= 'ReportMt5_Chelsi'
reportpath= path.abspath('ReportesMT5/')+'/'+ report_name + '.xlsx'

print(download_report(reportpath).get_report())

#if __name__ == "__main__":
    # print("Hello_World")
    #print(log.f_login())
    #print(log.account_info())
    #print(log.get_historical())
   #print(download_report(reportpath).get_report())


