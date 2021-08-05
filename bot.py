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
                if datetime.now(tz).strftime("%H:%M:%S") == "07:45:00":
                    staname = "TSUEN KING CIRCUIT MARKET"
                    route = "39M"

                if datetime.now(tz).strftime("%H:%M:%S") == "08:03:00":
                    staname = "CHUNG ON STREET TSUEN WAN"
                    route = "43P"

                if datetime.now(tz).strftime("%H:%M:%S") == "18:32:00":
                    staname = "FU WAH STREET TSUEN WAN"
                    route = "39M"
                if staname !="" and route !="":
                    df = checketa(route,staname)
                    if df != "":
                        text = "黎緊"+route+"係"+stationentotc[staname]+"開出時間係:\n"+df
                if text != "":
                    bot.sendMessage(chat_id=241767414, text=text)
                    time.sleep(1)

            # if event.get('httpMethod') == 'POST' and event.get('body'): 
            #     logger.info('Message received')
            #     update = telegram.Update.de_json(json.loads(event.get('body')), bot)
            #     chat_id = update.message.chat.id
            #     text = update.message.text

            #     if text == '/BusETA':
            #         pass
            #         text = "Hello, human! I am an echo bot, built with Python and the Serverless Framework."
        if str(time.time() - previous_time).split(".")[0] =="300":
            r = requests.get('https://booking.covidvaccine.gov.hk/forms/centre_data')
            data = r.json()
            TW = data["vaccines"][0]["regions"][2]["districts"][6]
            found =""
            for quote in TW["centers"][0]["quota"]:
                if str(quote['status']) == "1" or str(quote['status']) == "2":
                    found = found+ str(quote['date']) +"\n"

            if found != "":
                opening="以下日期%s有得book打針"%(TW["centers"][0]["cname"]) + "\n"
                found = opening +found
                bot.sendMessage(chat_id=241767414, text=found)
            previous_time = time.time()


            

if __name__=='__main__':
    main()







