import telebot
import schedule
import threading
import time
from datetime import datetime
import os

API_TOKEN = os.getenv('API_TOKEN')

bot = telebot.TeleBot(API_TOKEN)

# Stores chat states for users
user_state = {}

REMINDER_GIF_URL = "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExeWtxM25sZ2NlZHVnMHdlMDdnZTF6Mm45YTBxa3IybmN3ZzJ2MnBlNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/uX7EYxL3hhXoX6hK0N/giphy.gif"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_state[user_id] = {"waiting_for_ack": False, "reminder_time": "14:00", "reminder_interval": 60, "job": None}
    bot.reply_to(message, "Hiii I'm the little chuddy reminderer!")
    bot.send_message(chat_id=user_id, text="Commands: /time [time. like 14:00] to set reminder time, /interval [seconds] to set the spam interval")
    bot.send_message(chat_id=user_id, text="I'll send you reminders all day until you type 'ENOUGH BITCH' :3")
    bot.send_message(chat_id=user_id, text="(default reminder is at 2pm every minute)")
    schedule_reminder(user_id)
    
## Removes all scheduled jobs for the user.
def clear_existing_jobs(user_id):
    schedule.jobs[:] = [job for job in schedule.jobs if job.tags != {str(user_id)}]


## Schedule GIF reminders for the user starting from [reminder_time]
def schedule_reminder(user_id):
    clear_existing_jobs(user_id)
    job = schedule.every().day.at(user_state[user_id]["reminder_time"]).do(start_daily_reminder, user_id)
    user_state[user_id]["job"] = job


## Starts reminder loop.
def start_daily_reminder(user_id):
    if user_id not in user_state:
        return
    user_state[user_id]["waiting_for_ack"] = True
    send_reminders(user_id)

## Sends reminders every [reminder_interval] seconds until the user responds.
def send_reminders(user_id):
    def reminder_loop():
        while user_state.get(user_id, {}).get("waiting_for_ack"):
            bot.send_animation(user_id, REMINDER_GIF_URL, caption="take your meds!!! take your meds!!!")
            time.sleep(user_state[user_id]["reminder_interval"])

    threading.Thread(target=reminder_loop, daemon=True).start()

## Handles setting the reminder time in HH:MM format.
@bot.message_handler(commands=['time'])
def set_reminder_time(message):
    user_id = message.chat.id
    try:
        time_str = message.text.split()[1]
        datetime.strptime(time_str, "%H:%M")  # Validate time format
        user_state[user_id]["reminder_time"] = time_str
        bot.reply_to(message, f"Reminder time set to {time_str} yippee")
        schedule.clear(user_id)  # Clear previous schedules for this user
        schedule_reminder(user_id)  # Schedule the new reminder time
    except (IndexError, ValueError):
        bot.reply_to(message, "Stupid. You need to write it in HH:MM format, so like /time 14:30")

## Handles setting the reminder interval in seconds.
@bot.message_handler(commands=['interval'])
def set_reminder_interval(message):
    user_id = message.chat.id
    try:
        interval = int(message.text.split()[1])
        user_state[user_id]["reminder_interval"] = interval
        bot.reply_to(message, f"i'll spam you every {interval} seconds.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Stupid. You need to write seconds like /interval 300")

@bot.message_handler(func=lambda message: "ENOUGH BITCH GRR" in message.text)
def handle_response(message):
    user_id = message.chat.id
    if user_state.get(user_id, {}).get("waiting_for_ack"):
        bot.reply_to(message, "Okaaay sheesh... I'll return tomorrow thou!")
        user_state[user_id]["waiting_for_ack"] = False

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    threading.Thread(target=run_scheduler, daemon=True).start()
    bot.polling()

if __name__ == '__main__':
    main()
