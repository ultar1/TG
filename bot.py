import os
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler
from collections import defaultdict

app = Flask(__name__)

# Initialize the bot and dispatcher
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dispatcher = Dispatcher(bot, None, use_context=True)

# In-memory storage for user balances and referrals
user_balances = defaultdict(int)
user_referrals = defaultdict(list)

# Define the start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! I am your friendly Telegram bot. How can I assist you today?')

# Define the help command handler
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Here are the available commands:\n'
        '/start - Start the bot\n'
        '/help - Show this help message\n'
        '/about - About this bot\n'
        '/contact - Contact information\n'
        '/menu - Show the main menu'
    )

# Define the about command handler
def about(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('This is a friendly Telegram bot created to assist you with various tasks.')

# Define the contact command handler
def contact(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('You can contact us at support@example.com.')

# Define the menu command handler
def menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Join the main group", url="https://chat.whatsapp.com/J6FWyxJTPiQ21fbU29zg7L")],
        [InlineKeyboardButton("Referral program", callback_data='referral_program')],
        [InlineKeyboardButton("Generate your referral link", callback_data='generate_referral_link')],
        [InlineKeyboardButton("Check your balance", callback_data='check_balance')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Main Menu:', reply_markup=reply_markup)

# Define the referral program command handler
def referral_program(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Referral Program:\n'
        'Whenever you use your referral link to invite someone, you will earn 100 NGN for each successful invite.'
    )

# Define the generate referral link command handler
def generate_referral_link(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    referral_link = f'https://t.me/mazi?start={user_id}'
    update.message.reply_text(f'Your referral link: {referral_link}')

# Define the check balance command handler
def check_balance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    balance = user_balances[user_id]
    update.message.reply_text(f'Your balance: {balance} NGN')

# Define the callback query handler
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == 'referral_program':
        referral_program(update, context)
    elif query.data == 'generate_referral_link':
        generate_referral_link(update, context)
    elif query.data == 'check_balance':
        check_balance(update, context)

# Define the referral endpoint
@app.route('/referral/<int:user_id>', methods=['GET'])
def referral(user_id: int) -> str:
    user_balances[user_id] += 100
    return 'Referral successful!'

# Register the command handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(CommandHandler("about", about))
dispatcher.add_handler(CommandHandler("contact", contact))
dispatcher.add_handler(CommandHandler("menu", menu))
dispatcher.add_handler(CallbackQueryHandler(button))

@app.route('/')
def index() -> str:
    return 'Hello, this is the Telegram bot webhook server.'

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
