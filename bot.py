#!/usr/bin/env python
# coding: utf-8

import json
import logging
import requests
from zoneinfo import ZoneInfo
import holidays,pytz
import copy
from datetime import date, datetime,time,tzinfo
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Filters,Updater, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler
import uuid
import os

import configparser


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

STATION_LIST, ROUTE_ETA, TIME, PERIOD,MINUTE_1DIGI, MINUTE_2DIGI, ADD, REMOVE = range(8)


class bus_tg:
    def __init__(self, config,file_path):
        self.config = config
        self.token = self.config['TELEGRAM']['ACCESS_TOKEN']
        self.chat_id = self.config['TELEGRAM']['CHAT_ID']
        self.route_schedule = []
        self.route_list = {}
        self.direction = {'I':'inbound','O':'outbound'}
        self.reverse_direction = {'inbound':'I','outbound':'O'}
        self.station_list = {}
        self.alert_list = {}
        self.tz = ZoneInfo('Hongkong')
        self.hk_holidays = holidays.HK()
        self.daily_scan_time = time(17,0,0,0)  # equivalent to 1am HKT
        #self.daily_scan_time = time(6,00,0,0)
        self.file_path = file_path
        
        
    def start(self, update: Update, context: CallbackContext):
        chat_id = update.message.chat_id
        t = datetime(2022,12,14,22,15,00,000000,tzinfo=self.tz)
        t_utc = t.astimezone(pytz.utc)
        #context.job_queue.run_once(self.hello,t_utc, context=(chat_id,"yuasdgu"), name=str(chat_id))
        #print( context.job_queue.get_jobs_by_name(str(chat_id)))
        job_names = [job.name for job in context.job_queue.jobs()]
        print(job_names)
        
    def hello(self, update: Update,context: CallbackContext):
        chat_id, args = context.job.context

        #context.bot.send_message(chat_id, text='Beep!')
        context.job_queue.run_once(self.today_task,1,context=(self.chat_id,"yuasdgu"),name= str(uuid.uuid4()))

    def today_task(self,context: CallbackContext):
        chat_id = self.chat_id
        self.json_updater()
        t = datetime.now()
        t = t.astimezone(self.tz)
        
        today_day = t.day
        today_month = t.month
        today_year = t.year
        for alert_detail in self.alert_list["data"]:
            if alert_detail["period"] == "1":
                pass
            elif alert_detail["period"] == "2":
                print(t.date())
                print(t.weekday())
                if t.date() in self.hk_holidays:
                    continue

                if t.weekday() == 5 or t.weekday() == 6:
                    continue
            set_hour = alert_detail["time"][:2]
            set_minute = alert_detail["time"][2:]
            set_datetime = datetime(today_year,today_month,today_day,int(set_hour),int(set_minute),00,000000,tzinfo=self.tz)
            set_datetime_utc = set_datetime.astimezone(pytz.utc)
            #print("%s %s %s %s %s"%(alert_detail["route"][0],alert_detail["direction"],alert_detail["station"],str(set_datetime),str(set_datetime_utc)))
            context.job_queue.run_once(self.checkseteta,set_datetime_utc,context=(chat_id,json.dumps(alert_detail)),name=str(uuid.uuid4()))

    
    def checkseteta(self,context: CallbackContext):
        chat_id, args = context.job.context
        args = json.loads(args)
        
        #route_list = [{"route":args["route"][0],"direction":args["direction"]}]
        route_list = args["route_list"]
        url = self.config["URL"]["STOP_ETA"]+"%s"%(args["station"])
        eta_json = self.callAPI(url)["data"]
        df = self.checketa(eta_json,route_list)
        name_tc = self.stationID2tc(args["station"])
        
        if df != "":
            text = "黎緊以下路線係"+name_tc+"開出時間係:\n"+df
        else:
            text = "你查既路線暫時冇班次資訊"
        context.bot.send_message(chat_id, text=text)
    
    def checketa(self, eta_json,route_list):
        eta_dict = {}
        df = ""
        for eta in eta_json:
            eta_dict[eta["route"]] = {}
        try:
            for eta in eta_json:
                for route in route_list:
                    if eta['route'] == route["route"] and eta["dir"]== route["direction"]:
                        eta_dict[eta["route"]][eta["eta_seq"]] = eta['eta'].split("T")[1].split("+")[0]
        except:
            pass
        
        for k,v in eta_dict.items():
            if not v:
                continue
            df = df + k + ":\n"
            for i, eta_time in v.items():
                df = df +eta_time + "\n"
        return df

    def eta(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        callback_data = json.loads(query.data)

        route = callback_data["route"]
        direction = callback_data["bound"][:1]
        
        station = callback_data["stop"]
        name_tc = self.stationID2tc(station)
        route_list = [{"route":route,"direction":direction}]
        url = self.config["URL"]["STOP_ETA"]+"%s"%(station)

        eta_json = self.callAPI(url)["data"]

        df = self.checketa(eta_json,route_list)
        
        if df != "":
            text = "黎緊以下路線係"+name_tc+"開出時間係:\n"+df
        else:
            text = "你查既路線暫時冇班次資訊"

        query.edit_message_text(text)
        return ConversationHandler.END

    def stationID2tc(self, station_id):
        for station in self.station_list:
            if station["stop"] == station_id:
                return station["name_tc"]
        
    def route(self, update: Update, context: CallbackContext):
        try:
            query_message = update.message.text
            if "/alert" in query_message:
                route_id = context.args[0].upper().rstrip()
                handler_type = update.message.text.split(" ")[0]
            else:
                route_id = update.message.text.upper()
                handler_type = "/route"
            route_list = {}

            context.user_data["handler_type"] = handler_type
            temp_route_list = copy.deepcopy(self.route_list)
            for route_detail in temp_route_list:
                if route_detail["route"] == route_id and route_detail["service_type"] == '1':
                    dest = route_detail["dest_tc"]
                    route_detail.pop('orig_en')
                    route_detail.pop('orig_tc')
                    route_detail.pop('orig_sc')
                    route_detail.pop('dest_tc')
                    route_detail.pop('dest_sc')
                    route_detail.pop('dest_en')

                    route_list[dest] =route_detail
            if not route_list:
                update.message.reply_text("搵唔到你打既路線")
                return ConversationHandler.END
            button_list = [
                [InlineKeyboardButton(dest,callback_data=json.dumps(route)) for dest,route in route_list.items()]
                #[InlineKeyboardButton("A",callback_data= '1')]
            ]
            button_list.append([InlineKeyboardButton("取消",callback_data="cancel")])
            reply_markup = InlineKeyboardMarkup(button_list)
            update.message.reply_text("%s, Choose Direction"%(route_id), reply_markup=reply_markup)

            return STATION_LIST
        except (IndexError, ValueError):
            update.message.reply_text('Usage: /route <route>')
        
    def add(self, update: Update, context: CallbackContext):
        try:
            query = update.callback_query
            query.answer()
            #route = context.args[0]

            print(query.data)
            
        except (IndexError, ValueError):
            update.message.reply_text('Usage: /add <route>')
    
    def callAPI(self, URL):
        r = requests.get(URL)
        return r.json()
    
    def load_file(self):
        f = open(os.path.join(self.file_path,"route.json"),"r")
        self.route_list = json.loads(f.read())["data"]
        f.close()
        f = open(os.path.join(self.file_path,"station.json"),"r")
        self.station_list = json.loads(f.read())["data"]
        f.close()
        f = open(os.path.join(self.file_path,"alert.json"),"r")
        self.alert_list = json.loads(f.read())
        f.close()
        
    def station(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = query.data
        self.cancel(text,query)
        handler_type = context.user_data["handler_type"]

        callback_data = json.loads(text)
        route_id = callback_data["route"]
        direction = self.direction[callback_data["bound"]]
        service_type = callback_data["service_type"]
        station_list_url = self.config["URL"]["ROUTE_STOP"]+('%s/%s/%s')%(route_id,direction,service_type)
        station_list = self.callAPI(station_list_url)["data"]
        for station_detail in station_list:

            station_detail.pop('seq')
            station_detail["bound"] += station_detail["service_type"]
            station_detail.pop('service_type')
        button_list = []
        for route_station in station_list:
            name_tc = [station["name_tc"] for station in self.station_list if station["stop"] == route_station["stop"]][0]
            button_list.append([InlineKeyboardButton(name_tc,callback_data=json.dumps(route_station))])
        button_list.append([InlineKeyboardButton("取消",callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(button_list)
        #reply_markup.add(InlineKeyboardButton("1", callback_data=str(1)))
        #reply_markup.add(InlineKeyboardButton("2", callback_data=str(2)))
        query.edit_message_text("%s, Choose Station"%(route_id), reply_markup=reply_markup)
        
        if handler_type == "/route":
            return ROUTE_ETA
        elif handler_type == "/alert":
            return TIME
        
    def alert_time(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = query.data
        self.cancel(text,query)
        callback_data = json.loads(text)
        button_list = []
        sub_button_list = []
        context.user_data["route"] = callback_data["route"]
        context.user_data["direction"] = callback_data["bound"][:1]
        context.user_data["service_type"] = callback_data["bound"][1:]
        context.user_data["station"] = callback_data["stop"]
        for hour in range(24):
            if hour < 10:
                mod_hour = "0"+str(hour)
                sub_button_list.append(InlineKeyboardButton(mod_hour,callback_data=mod_hour))
            else:
                sub_button_list.append(InlineKeyboardButton(str(hour),callback_data=str(hour)))
            if (hour+1) % 3==0:
                button_list.append(sub_button_list)
                sub_button_list = []
        button_list.append([InlineKeyboardButton("取消",callback_data="cancel")])
        reply_markup=InlineKeyboardMarkup(button_list)
        query.edit_message_text("請選擇希望幫你檢查既小時", reply_markup=reply_markup)
        #query.edit_message_text("請輸入希望幫你檢查既時間, 例: 2030")
        return MINUTE_1DIGI
    
    def minute_1digi(self, update:Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = query.data
        self.cancel(text,query)
        context.user_data["hour"] = text
        sub_button_list =[]
        button_list =[]
        for minute in range(0,60,10):
            if minute == 0:
                sub_button_list.append(InlineKeyboardButton("00",callback_data="00"))
            else:
                sub_button_list.append(InlineKeyboardButton(str(minute),callback_data=str(minute)))
            if (minute+10) % 30 == 0:
                button_list.append(sub_button_list)
                sub_button_list = []
        button_list.append([InlineKeyboardButton("取消",callback_data="cancel")])
        reply_markup=InlineKeyboardMarkup(button_list)
        query.edit_message_text("請選擇希望幫你檢查既分鐘", reply_markup=reply_markup)
        return MINUTE_2DIGI
    
    def minute_2digi(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = query.data
        self.cancel(text,query)
        minute = int(text)
        sub_button_list =[]
        button_list =[]
        for minute in range(minute,minute+10):
            sub_button_list.append(InlineKeyboardButton(str(minute),callback_data=str(minute)))
            if (minute+1) % 2 == 0:
                button_list.append(sub_button_list)
                sub_button_list = []
        button_list.append([InlineKeyboardButton("取消",callback_data="cancel")])
        reply_markup=InlineKeyboardMarkup(button_list)
        query.edit_message_text("請選擇希望幫你檢查既分鐘", reply_markup=reply_markup)
        return PERIOD

    def alert_period(self, update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = query.data
        self.cancel(text,query)
        if len(text) == 1:
            text = "0"+text
        context.user_data["minute"] = text
        context.user_data["time"] = context.user_data["hour"]+context.user_data["minute"]
        print(context.user_data["time"])
        button_list =[]
        sub_button_list =[]
        sub_button_list.append(InlineKeyboardButton("每日通知",callback_data="1"))
        sub_button_list.append(InlineKeyboardButton("返工日通知",callback_data="2"))
        button_list.append(sub_button_list)
        button_list.append([InlineKeyboardButton("取消",callback_data="cancel")])
        reply_markup=InlineKeyboardMarkup(button_list)
        query.edit_message_text("好, 係每日通知你定返工日先通知?", reply_markup=reply_markup)
        return ADD
        # if len(text) == 4:
        #     if text.isnumeric():
        #         text = text[:2] + ":" +text[2:]
        #         update.message.reply_text("%s, 好, 係每日通知你定返工日先通知, 輸入'1' 係每日通知, '2'係返工日通知"%(text))
        #         return ADD
        #     else:
        #         update.message.reply_text("你輸入既唔係數字黎，請重新開始")
        #         return ConversationHandler.END
        # else:
        #     update.message.reply_text("你輸入的格式錯誤，請重新開始")
        #     return ConversationHandler.END
    
    def add(self, update:Update, context: CallbackContext):
        query = update.callback_query
        query.answer()
        text = query.data
        self.cancel(text,query)
        if text == "1" or text == "2":
            context.user_data["period"] = text
            context.user_data.pop('handler_type')
            context.user_data["route_list"] = []
            route_alert_info = {
                "route":context.user_data["route"],
                "direction":context.user_data["direction"],
                "service_type":context.user_data["service_type"]
                }
            context.user_data.pop("route")
            context.user_data.pop("direction")
            context.user_data.pop("service_type")
            context.user_data.pop("hour")
            context.user_data.pop("minute")
            print(context.user_data)

            self.grouping(route_alert_info,context)
            print(self.alert_list)
            self.save_alert_list()
            query.edit_message_text("搞掂")
            return ConversationHandler.END

    def grouping(self, route_alert_info,context):
        for i,alert_station in enumerate(self.alert_list["data"]):
            if context.user_data["station"] == alert_station["station"] and context.user_data["time"] == alert_station["time"] and context.user_data["period"] == alert_station["period"]:
                self.alert_list["data"][i]["route_list"].append(route_alert_info.copy())
                return
        context.user_data["route_list"].append(route_alert_info)
        self.alert_list["data"].append(context.user_data.copy())
        return 
    
    def save_alert_list(self):
        with open(os.path.join(self.file_path,'alert.json'),'w') as f:
            f.write(json.dumps(self.alert_list))

        
    def remove(self, update:Update, context: CallbackContext):
        df = "以下係你希望我會通知你既路線, 如果想取消就撳相應既數字\n"
        index = 1
        alert_period = {
            "1":"每日通知",
            "2":"返工日通知"
        }
        button_list = []
        sub_button_list = []
        for alert_num,alert_detail in enumerate(self.alert_list["data"]):
            print(alert_num+1 ==len(self.alert_list["data"]))
            station = alert_detail["station"]
            period = alert_detail["period"]
            alert_time = alert_detail["time"]
            for i,route_info in enumerate(alert_detail["route_list"]):
                route = route_info["route"]
                direction = route_info["direction"]
                service_type = route_info["service_type"]
                route_list = ""
                route_detail = self.routeStation2detail(route,direction,service_type)
                dest_tc = route_detail["dest_tc"]
                name_tc = self.stationID2tc(station)
                df += "%s: 路線: %s 目的地: %s 巴士站: %s 通知時間: %s %s\n"%(str(index),route,dest_tc, name_tc, alert_time,alert_period[period])
                sub_button_list.append(InlineKeyboardButton(str(index),callback_data=str(index)))
                if index %3 ==0 or (alert_num+1 ==len(self.alert_list["data"]) and i+1==len(alert_detail["route_list"])):
                    button_list.append(sub_button_list)
                    sub_button_list=[]
                index+=1
        button_list.append([InlineKeyboardButton("取消",callback_data="cancel")])
        reply_markup=InlineKeyboardMarkup(button_list)
        update.message.reply_text(df,reply_markup=reply_markup)
        return REMOVE
    
    def removefromList(self, update:Update, context: CallbackContext ):
        query = update.callback_query
        query.answer()
        text = query.data
        self.cancel(text,query)
        if text.isnumeric():
            index = int(text)
            for i,alert_list_data in enumerate(self.alert_list["data"]):
                index = index - len(alert_list_data["route_list"])
                if index <= 0:
                    if len(alert_list_data["route_list"]) ==1:
                        self.alert_list["data"].pop(i)
                    else:
                        self.alert_list["data"][i]["route_list"].pop(index-1)
                    self.save_alert_list()
                    query.edit_message_text("Del左")
                    return ConversationHandler.END
                    
    def routeStation2detail(self,_route, _direction, _service_type):
        for route_detail in self.route_list:

            if route_detail["route"] == _route and route_detail["bound"] == _direction and route_detail["service_type"] == _service_type:
                return route_detail
    
    def test(self, update:Update, context: CallbackContext ):
        chat_id = update.message.chat_id

        context.job_queue.run_once(self.hello,10, context=(chat_id,"yuasdgu"), name=str(chat_id))

    def json_updater(self):
        self.station_list = self.callAPI(config["URL"]["STOP"])["data"]
        self.route_list = self.callAPI(config["URL"]["ROUTE"])["data"]
        
    def cancel(self, text,query):
        if text == "cancel":
            query.edit_message_text("取消")
            return ConversationHandler.END
    
    def main(self):
        
        self.load_file()
        self.updater = Updater(self.token)
        self.dispatcher = self.updater.dispatcher
        self.updater.job_queue.run_once(self.today_task,5,context=(self.chat_id,"yuasdgu"),name= "init_task")
        self.updater.job_queue.run_daily(self.today_task,self.daily_scan_time,days=(0, 1, 2, 3, 4, 5, 6),context=(self.chat_id,"yuasdgu"),name= "daily task")

        
        #Add different command
        route_handler = ConversationHandler(
            #entry_points = [CommandHandler('route',self.route)],
            entry_points = [MessageHandler(Filters.text & ~(Filters.command | Filters.regex('^Done$')),self.route)],
            states={
                STATION_LIST: [
                    CallbackQueryHandler(self.station),
                ],
                ROUTE_ETA: [
                    CallbackQueryHandler(self.eta),
                ]
                
            },
            fallbacks=[CommandHandler('route',self.route)],
        )
        
        alert_handler = ConversationHandler(
            entry_points = [CommandHandler('alert',self.route)],
            states={
                STATION_LIST: [
                    CallbackQueryHandler(self.station),
                ],
                TIME: [
                    CallbackQueryHandler(self.alert_time)
                ],
                MINUTE_1DIGI: [
                    CallbackQueryHandler(self.minute_1digi)
                ],
                MINUTE_2DIGI: [
                    CallbackQueryHandler(self.minute_2digi)
                ],
                PERIOD: [
                    CallbackQueryHandler(self.alert_period)
                ],
                ADD: [
                    CallbackQueryHandler(self.add)
                ]
            },
            fallbacks=[CommandHandler('alert',self.route)],
        )
        
        remove_handler = ConversationHandler(
            entry_points = [CommandHandler("remove",self.remove)],
            states={
                REMOVE: [
                    CallbackQueryHandler(self.removefromList)
                ]
            },
            fallbacks=[CommandHandler("remove",self.remove)],
        )
        
        self.dispatcher.add_handler(CommandHandler("start",self.start))
        self.dispatcher.add_handler(route_handler)
        self.dispatcher.add_handler(alert_handler)
        self.dispatcher.add_handler(CommandHandler("check",self.hello))
        self.dispatcher.add_handler(remove_handler)
        
        #Start the Bot
        self.updater.start_polling()
        
        self.updater.idle()
        
file_path = os.path.dirname(os.path.realpath(__file__))        

# Load config
config = configparser.ConfigParser()
config.read(os.path.join(file_path,'config.ini'))

a = bus_tg(config,file_path)
a.main()





