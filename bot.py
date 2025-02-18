import os
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0)

# Initialize the database
db.create_all()

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
        [InlineKeyboardButton("Generate your referral link", callback_data='generate_referral_link')],
        [InlineKeyboardButton("Check your balance", callback_data='check_balance')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Main Menu:', reply_markup=reply_markup)

# Define the generate referral link command handler
def generate_referral_link(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    referral_link = f'https://your-app.onrender.com/referral/{user_id}/{user_id}'
    update.message.reply_text(f'Your referral link: {referral_link}')

# Define the check balance command handler
def check_balance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user = User.query.filter_by(telegram_id=str(user_id)).first()
    balance = user.balance if user else 0
    update.message.reply_text(f'Your balance: {balance} NGN')

# Define the callback query handler
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == 'generate_referral_link':
        generate_referral_link(query, context)
    elif query.data == 'check_balance':
        check_balance(query, context)

# Define the referral endpoint
@app.route('/referral/<int:inviter_id>/<int:new_user_id>', methods=['GET'])
def referral(inviter_id: int, new_user_id: int) -> str:
    inviter = User.query.filter_by(telegram_id=str(inviter_id)).first()
    new_user = User.query.filter_by(telegram_id=str(new_user_id)).first()

    if not inviter:
        inviter = User(telegram_id=str(inviter_id), balance=100)
        db.session.add(inviter)
    else:
        inviter.balance += 100

    if not new_user:
        new_user = User(telegram_id=str(new_user_id), balance=100)
        db.session.add(new_user)
    else:
        new_user.balance += 100

    db.session.commit()

    # Notify the inviter
    bot.send_message(chat_id=inviter_id, text=f"Someone used your referral link! Your new balance is {inviter.balance} NGN.")

    # Notify the new user
    bot.send_message(chat_id=new_user_id, text=f"Welcome! You have received 100 NGN for joining. Your balance is {new_user.balance} NGN.")

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
