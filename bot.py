import os
import random
import time
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from flask_sqlalchemy import SQLAlchemy
from pytube import YouTube
import openai
from PIL import Image
from moviepy.editor import VideoFileClip

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Integer, default=0)
    phone_number = db.Column(db.String(20), nullable=True)
    network = db.Column(db.String(20), nullable=True)

# Initialize the database
db.create_all()

# Initialize the bot and dispatcher
bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dispatcher = Dispatcher(bot, None, use_context=True)

# Define the start command handler with captcha
def start(update: Update, context: CallbackContext) -> None:
    num1, num2 = random.randint(1, 10), random.randint(1, 10)
    context.user_data['captcha_answer'] = num1 + num2
    update.message.reply_text(f'Welcome! Please solve this math problem to proceed: {num1} + {num2} = ?')

# Define the captcha handler
def handle_captcha(update: Update, context: CallbackContext) -> None:
    try:
        user_answer = int(update.message.text)
        if user_answer == context.user_data.get('captcha_answer'):
            show_main_menu(update, context)
        else:
            num1, num2 = random.randint(1, 10), random.randint(1, 10)
            context.user_data['captcha_answer'] = num1 + num2
            update.message.reply_text(f'Incorrect. Please try again: {num1} + {num2} = ?')
    except ValueError:
        update.message.reply_text('Please enter a valid number.')

# Show the main menu
def show_main_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Referral link", callback_data='generate_referral_link')],
        [InlineKeyboardButton("Check your balance", callback_data='check_balance')],
        [InlineKeyboardButton("Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("Download YouTube Video", callback_data='download_video')],
        [InlineKeyboardButton("Upscale Image", callback_data='upscale_image')],
        [InlineKeyboardButton("Compress Video", callback_data='compress_video')],
        [InlineKeyboardButton("Ask GPT", callback_data='ask_gpt')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Main Menu:', reply_markup=reply_markup)

    # Add commands to the keyboard
    keyboard_buttons = [
        [KeyboardButton("/generate_referral_link")],
        [KeyboardButton("/check_balance")],
        [KeyboardButton("/withdraw")],
        [KeyboardButton("/download_video")],
        [KeyboardButton("/upscale_image")],
        [KeyboardButton("/compress_video")],
        [KeyboardButton("/ask_gpt")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_buttons, one_time_keyboard=True)
    update.message.reply_text('Use the commands below:', reply_markup=reply_markup)

# Define the help command handler
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Here are the available commands:\n'
        '/start - Start the bot\n'
        '/help - Show this help message\n'
        '/about - About this bot\n'
        '/contact - Contact information\n'
        '/menu - Show the main menu\n'
        '/withdraw - Withdraw funds\n'
        '/download - Download YouTube video\n'
        '/ask_gpt - Ask GPT-4 a question'
    )

# Define the about command handler
def about(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('This is a friendly Telegram bot created to assist you with various tasks.')

# Define the contact command handler
def contact(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('You can contact us at support@example.com.')

# Define the menu command handler
def menu(update: Update, context: CallbackContext) -> None:
    show_main_menu(update, context)

# Define the generate referral link command handler
def generate_referral_link(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    referral_link = f'https://t.me/Maziul_bot?start={user_id}'
    update.message.reply_text(f'Your referral link: {referral_link}')

# Define the check balance command handler
def check_balance(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user = User.query.filter_by(telegram_id=str(user_id)).first()
    balance = user.balance if user else 0
    update.message.reply_text(f'Your balance: {balance} NGN')

# Define the withdraw command handler
def withdraw(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user = User.query.filter_by(telegram_id=str(user_id)).first()
    if not user:
        user = User(telegram_id=str(user_id))
        db.session.add(user)
        db.session.commit()
    context.user_data['withdraw_step'] = 'phone_number'
    update.message.reply_text('Please send your phone number and network (e.g. 09100000000, MTN)')

# Define the message handler for withdrawal process
def handle_withdraw(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user = User.query.filter_by(telegram_id=str(user_id)).first()
    try:
        if context.user_data.get('withdraw_step') == 'phone_number':
            phone_number, network = update.message.text.split(', ')
            user.phone_number = phone_number
            user.network = network
            db.session.commit()
            context.user_data['withdraw_step'] = 'amount'
            update.message.reply_text('Phone number and network saved. Please enter the amount you want to withdraw.')
        elif context.user_data.get('withdraw_step') == 'amount':
            amount = int(update.message.text)
            if amount > user.balance:
                update.message.reply_text('Error: The amount exceeds your available balance.')
            else:
                user.balance -= amount
                db.session.commit()
                update.message.reply_text(f'Success: {amount} NGN has been withdrawn. Your new balance is {user.balance} NGN.')
    except ValueError:
        update.message.reply_text('Please enter a valid input.')

# Define the download video command handler
def download_video(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please send the YouTube URL of the video you want to download.')

# Define the message handler for downloading YouTube videos
def handle_download(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    try:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        stream.download(output_path='downloads/', filename=f'{yt.title}.mp4')
        update.message.reply_text(f'Success! The video "{yt.title}" has been downloaded.')
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

# Define the ask command handler for GPT-4
def ask(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please ask your question.')

# Define the message handler for GPT-4
def handle_ask(update: Update, context: CallbackContext) -> None:
    question = update.message.text
    try:
        response = openai.Completion.create(
            engine="text-davinci-004",
            prompt=question,
            max_tokens=150
        )
        answer = response.choices[0].text.strip()
        update.message.reply_text(answer)
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

# Define the upscale image command handler
def upscale_image(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please send the image you want to upscale.')

# Define the message handler for upscaling images
def handle_upscale_image(update: Update, context: CallbackContext) -> None:
    photo = update.message.photo[-1].get_file()
    photo.download('image.jpg')
    img = Image.open('image.jpg')
    img = img.resize((img.width * 2, img.height * 2), Image.ANTIALIAS)
    img.save('upscaled_image.jpg')
    update.message.reply_photo(photo=open('upscaled_image.jpg', 'rb'))

# Define the compress video command handler
def compress_video(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please send the video you want to compress.')

# Define the message handler for compressing videos
def handle_compress_video(update: Update, context: CallbackContext) -> None:
    video = update.message.video.get_file()
    video.download('video.mp4')
    clip = VideoFileClip('video.mp4')
    clip_resized = clip.resize(height=360)
    clip_resized.write_videofile('compressed_video.mp4', codec='libx264')
    update.message.reply_video(video=open('compressed_video.mp4', 'rb'))

# Define the tag command handler
def tag(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    members = bot.get_chat_administrators(chat_id)
    tags = " ".join([f"@{member.user.username}" for member in members if member.user.username])
    if tags:
        update.message.reply_text(f"Attention: {tags}")
    else:
        update.message.reply_text("No members with usernames found to tag.")

# Define the callback query handler
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    if query.data == 'generate_referral_link':
        generate_referral_link(query, context)
    elif query.data == 'check_balance':
        check_balance(query, context)
    elif query.data == 'withdraw':
        withdraw(query, context)
    elif query.data == 'download_video':
        download_video(query, context)
    elif query.data == 'upscale_image':
        upscale_image(query, context)
    elif query.data == 'compress_video':
        compress_video(query, context)
    elif query.data == 'ask_gpt':
        ask(query, context)

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
dispatcher.add_handler(CommandHandler("withdraw", withdraw))
dispatcher.add_handler(CommandHandler("download", download_video))
dispatcher.add_handler(CommandHandler("ask", ask))
dispatcher.add_handler(CommandHandler("upscale_image", upscale_image))
dispatcher.add_handler(CommandHandler("compress_video", compress_video))
dispatcher.add_handler(CommandHandler("tag", tag))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_captcha))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_withdraw))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_download))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_ask))
dispatcher.add_handler(MessageHandler(Filters.photo & ~Filters.command, handle_upscale_image))
dispatcher.add_handler(MessageHandler(Filters.video & ~Filters.command, handle_compress_video))

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
