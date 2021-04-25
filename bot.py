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
route_url = "https://data.etabus.gov.hk/v1/transport/kmb/route/39M"


route_stop = "https://data.etabus.gov.hk/v1/transport/kmb/route-stop/%s/outbound/1"%("39M")
stop = "https://data.etabus.gov.hk/v1/transport/kmb/route/%s/outbound/1"%("39M")
route = "https://data.etabus.gov.hk/v1/transport/kmb/route-eta/%s/1"%("39M") 


# station_list = requests.get("https://data.etabus.gov.hk/v1/transport/kmb/stop")

# for i in station_list.json()['data']:
#     if i['name_en'] == 'FU WAH STREET TSUEN WAN':
#         print(i['stop'])

    

station = {
    "ALLWAY GARDENS BUS TERMINUS" : "756141FB7A6EA349",
    "TSUEN KING CIRCUIT MARKET" : "FE30EA565CC9ADBE",
    "FU WAH STREET TSUEN WAN" : "D711AFA9658D51E9",
    "CHUNG ON STREET TSUEN WAN" : "CA793BE80FF68AE2"
}

stationentotc = {
    "ALLWAY GARDENS BUS TERMINUS" : "荃威花園巴士線站",
    "TSUEN KING CIRCUIT MARKET" : "荃景圍街市",
    "FU WAH STREET TSUEN WAN" : "富華街",
    "CHUNG ON STREET TSUEN WAN" : "眾安街"
}


tz = pytz.timezone('Hongkong')
hk_holidays = holidays.HK()

def configure_telegram():
    """
    Configures the bot with a Telegram Token.
    Returns a bot instance.
    """

    TELEGRAM_TOKEN = '1777615156:AAFhKEa9wRQf2Txif8fC6RgpK13q6OhrMw8'
    if not TELEGRAM_TOKEN:
        logger.error('The TELEGRAM_TOKEN must be set')
        raise NotImplementedError

    return telegram.Bot(TELEGRAM_TOKEN)

bot = configure_telegram()
#Only runs in working day

def checketa(route,station):
    stop = requests.get("https://data.etabus.gov.hk/v1/transport/kmb/stop-eta/%s"%(station[station]))
    df=""
    for i in stop.json()['data']:
        if i['route'] == route:
            df = df + (i['route']+" " +i['eta'].split("T")[1].split("+")[0] + "\n")
    return df


def main():
    while True:
        today = date.today()
        staname = ""
        route = ""
        if not today in hk_holidays:
            text = ""
            if datetime.now(tz).strftime("%H:%M:%S") == "14:55:00":
                staname = "TSUEN KING CIRCUIT MARKET"
                route = "39M"

            if datetime.now(tz).strftime("%H:%M:%S") == "14:57:00":
                staname = "CHUNG ON STREET TSUEN WAN"
                route = "43P"

            if datetime.now(tz).strftime("%H:%M:%S") == "18:30:00":
                staname = "FU WAH STREET TSUEN WAN"
                route = "39M"
            if staname !="" and route !="":
                df = checketa(route,staname)
                text = "黎緊"+route+"係"+stationentotc[staname]+"開出時間係:/n"+df
            if text != "":
                bot.sendMessage(chat_id=241767414, text=text)

        # if event.get('httpMethod') == 'POST' and event.get('body'): 
        #     logger.info('Message received')
        #     update = telegram.Update.de_json(json.loads(event.get('body')), bot)
        #     chat_id = update.message.chat.id
        #     text = update.message.text

        #     if text == '/BusETA':
        #         pass
        #         #text = "Hello, human! I am an echo bot, built with Python and the Serverless Framework."

if __name__=='__main__':
    main()







