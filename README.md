# Bus-Estimate-Time-Arrival-Telegram-Alert
An alert to get Hong Kong bus estimate time arrival and send alert to telegram

# Usage
Monitor the estimated time arrival of KMB bus at specific bus stop at specific time. Push message to telegram channel to alert user when is the next bus. Useful to know the coming bus arrival time before getting out from home every working day. 
![image](https://user-images.githubusercontent.com/75830784/146629000-46b1f6f8-bd48-435e-a876-194db8a8595f.png)


# How to use
1. Git clone the repository
2. Pip install the packages in requirements.txt
3. Set the bus route and station you want to monitor in bot.py
4. Get a telegram bot from telegram BotFather. 
5. Copy the Token and paste to bot.py
6. Create a new channel and add the bot into the channel
7. Get the chat id, https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id
8. Copy and paste the chat id to bot.py
9. RUN!

# Heroku
This program can be deployed to Heroku so you don't have to turn on a computer all the time. The required files are in the repository. Follow "How to use" to setup and push to Heroku.
