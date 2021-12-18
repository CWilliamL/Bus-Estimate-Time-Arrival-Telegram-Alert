import requests
import pytz, holidays
from datetime import date, datetime
from telegram.ext import Updater, CommandHandler
import time
import telegram

url = "https://data.etabus.gov.hk/v1/transport/kmb/stop"
route_stop_url = "https://data.etabus.gov.hk/v1/transport/kmb/route-stop/{route}/{direction}/{service_type}"

stop_ETA_url ="https://data.etabus.gov.hk/v1/transport/kmb/stop-eta/{stop_id}"
route_ETA_url = "https://data.etabus.gov.hk/v1/transport/kmb/route-eta/{route}/{service_type}"
stop_url = "https://data.etabus.gov.hk/v1/transport/kmb/route/{route}/{direction}/{service_type}"
   

station = {
	#Get Wanted Station ID from https://data.etabus.gov.hk/v1/transport/kmb/stop
    #"FU WAH STREET TSUEN WAN" : "D711AFA9658D51E9",

}

stationentotc = {
	#Translate station name to Traditional Chinese Character
    #"FU WAH STREET TSUEN WAN" : "富華街",

}


tz = pytz.timezone('Hongkong')
hk_holidays = holidays.HK()

def configure_telegram():
    """
    Configures the bot with a Telegram Token.
    Returns a bot instance.
    """

    TELEGRAM_TOKEN = 'Your Telegram Token'
    if not TELEGRAM_TOKEN:
        logger.error('The TELEGRAM_TOKEN must be set')
        raise NotImplementedError

    return telegram.Bot(TELEGRAM_TOKEN)

bot = configure_telegram()
#Only runs in working day

def checketa(route,staname):

    stop = requests.get("https://data.etabus.gov.hk/v1/transport/kmb/stop-eta/%s"%(station[staname]))
    df=""

    for i in stop.json()['data']:
        try:
            if i['route'] == route:
                df = df + (i['eta'].split("T")[1].split("+")[0] + "\n")
        except:
            pass
    return df


def main():
    previous_time = time.time()
    while True:

        dtobj1=datetime.utcnow() 
        dtobj3=dtobj1.replace(tzinfo=pytz.UTC)
        today=dtobj3.astimezone(pytz.timezone("Asia/Hong_Kong"))
        
        staname = ""
        route = ""
        if not today in hk_holidays:
            if today.weekday() != 5 and today.weekday() != 6:
                text = ""
				
				#Example to set your own alert
                #if datetime.now(tz).strftime("%H:%M:%S") == "08:03:00":
                #    staname = "CHUNG ON STREET TSUEN WAN"
                #    route = "43P"
                
				if staname !="" and route !="":
                    df = checketa(route,staname)
                    if df != "":
                        text = "黎緊"+route+"係"+stationentotc[staname]+"開出時間係:\n"+df
                if text != "":
                    bot.sendMessage(chat_id="Your telegram channel ID", text=text)
                    time.sleep(1)

            previous_time = time.time()
		time.sleep(0.1)

            

if __name__=='__main__':
    main()







