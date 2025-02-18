import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

app = Flask(__name__)

# Initialize the bot and dispatcher
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dispatcher = Dispatcher(bot, None, use_context=True)

# Define the start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your bot.')

# Register the /start command handler
dispatcher.add_handler(CommandHandler("start", start))

@app.route('/webhook', methods=['POST'])
def webhook() -> str:
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

def set_webhook():
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("No WEBHOOK_URL found in environment variables")
    bot.set_webhook(webhook_url)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
