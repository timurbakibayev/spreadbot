import json
import gspread
from oauth2client.client import SignedJwtAssertionCredentials
from multiprocessing import Process
import time

json_key = json.load(open('spreadbot_key.json'))
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope) # get email and key from creds

def check(file):
    while True:
        subscribers = []

        try:
            subscribers_file = json.load(open('subscribers.json'))
            subscribers = subscribers_file["subscribers"]
            # print("subscribers loaded", subscribers)
        except:
            json.dump({"subscribers": []}, open("subscribers.json", "w"))

        for subscriber in subscribers:
            status = {}
            status_filename = f'status{subscriber}.json'
            try:
                status = json.load(open(status_filename))
                # print("last status loaded", status)
            except:
                json.dump({"fake": "fake"}, open(status_filename, "w"))

            # print("checking for", subscriber)
            # bot.send_message(subscriber, 'Checking')
            spreadsheet = file.open("all_courses")
            for sheet in spreadsheet.worksheets():
                # print("Next sheet", str(sheet.title), sheet.id)
                # print("Records:", sheet.row_count)
                if str(sheet.id) not in status:
                    status[str(sheet.id)] = 0
                if status[str(sheet.id)] < int(sheet.row_count):
                    bot.send_message(subscriber, f'You have {min(int(sheet.row_count) - status[str(sheet.id)], int(sheet.row_count)-1)} '
                                                 f'new records in {str(sheet.title)}')
                    recs = sheet.get_all_records()
                    msg = ""
                    for record in recs[max(len(recs) - (int(sheet.row_count)-status[str(sheet.id)]),0):]:
                        for key in record:
                            if len(str(record[key])) > 0:
                                msg += f"{key}: {record[key]}\n"
                        msg += "\n"
                    bot.send_message(subscriber, msg)
                status[sheet.id] = int(sheet.row_count)

            json.dump(status, open(status_filename, "w"))
            time.sleep(5)

# check(gspread.authorize(credentials))

import telebot

bot = telebot.TeleBot(json_key["telegram"])

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Enter password')

@bot.message_handler(content_types=['text'])
def send_text(message):
    subscribers = []

    try:
        subscribers_file = json.load(open('subscribers.json'))
        subscribers = subscribers_file["subscribers"]
        print("subscribers loaded", subscribers)
    except:
        json.dump({"subscribers": []}, open("subscribers.json", "w"))

    if message.text.lower() == 'iddqd':
        bot.send_message(message.chat.id, 'Correct, you''ve been added to notifications. Type stop to stop.')
        subscribers.append(message.chat.id)
        json.dump({"subscribers": subscribers}, open("subscribers.json", "w"))
    elif message.text.lower() == 'stop':
        bot.send_message(message.chat.id, 'Stopping')
        subscribers.remove(message.chat.id)
        json.dump({"subscribers": subscribers}, open("subscribers.json", "w"))
    else:
        bot.send_message(message.chat.id, 'I don''t get it.')
    # elif message.text.lower() == 'пока':
    #     bot.send_message(message.chat.id, 'Прощай, создатель')
    # elif message.text.lower() == 'я тебя люблю':
    #     bot.send_sticker(message.chat.id, 'CAADAgADZgkAAnlc4gmfCor5YbYYRAI')

p1 = Process(target=check, args=(gspread.authorize(credentials),))
p1.start()
print("Process started")
bot.polling(none_stop=True)
