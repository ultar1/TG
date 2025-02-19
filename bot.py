import os
import random
import requests
from flask import Flask, request
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ChatPermissions
from telegram.ext import Dispatcher, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
from flask_sqlalchemy import SQLAlchemy
import openai
from PIL import Image, ImageEnhance
from moviepy.editor import VideoFileClip
from pydub import AudioSegment

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

# Define the start command handler
def start(update: Update, context: CallbackContext) -> None:
    show_main_menu(update, context)

# Show the main menu
def show_main_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🔗 Referral link", callback_data='generate_referral_link')],
        [InlineKeyboardButton("💰 Check balance", callback_data='check_balance')],
        [InlineKeyboardButton("💸 Withdraw", callback_data='withdraw')],
        [InlineKeyboardButton("🖼️ Upscale image", callback_data='upscale_image')],
        [InlineKeyboardButton("🎥 Compress video", callback_data='compress_video')],
        [InlineKeyboardButton("🤖 Ask GPT", callback_data='ask_gpt')],
        [InlineKeyboardButton("🎵 Play music", callback_data='play_music')],
        [InlineKeyboardButton("🌦️ Weather", callback_data='weather')],
        [InlineKeyboardButton("📰 News", callback_data='news')],
        [InlineKeyboardButton("🌐 Translate", callback_data='translate')],
        [InlineKeyboardButton("😂 Joke", callback_data='joke')],
        [InlineKeyboardButton("👥 Group menu", callback_data='group_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('📋 **Main Menu**', reply_markup=reply_markup, parse_mode='Markdown')

    # Add commands to the keyboard
    keyboard_buttons = [
        [KeyboardButton("🔗 /generate_referral_link")],
        [KeyboardButton("💰 /check_balance")],
        [KeyboardButton("💸 /withdraw")],
        [KeyboardButton("🖼️ /upscale_image")],
        [KeyboardButton("🎥 /compress_video")],
        [KeyboardButton("🤖 /ask_gpt")],
        [KeyboardButton("🎵 /play_music")],
        [KeyboardButton("🌦️ /weather")],
        [KeyboardButton("📰 /news")],
        [KeyboardButton("🌐 /translate")],
        [KeyboardButton("😂 /joke")],
        [KeyboardButton("👥 /group_menu")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard_buttons, one_time_keyboard=True)
    update.message.reply_text('Use the commands below:', reply_markup=reply_markup)

# Define the group menu command handler
def group_menu(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🔔 Tag", callback_data='tag')],
        [InlineKeyboardButton("🔇 Mute", callback_data='mute')],
        [InlineKeyboardButton("🚫 Antilink", callback_data='antilink')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('👥 **Group Menu**', reply_markup=reply_markup, parse_mode='Markdown')

# Define the help command handler
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Here are the available commands:\n'
        '🔗 /generate_referral_link - Generate your referral link\n'
        '💰 /check_balance - Check your balance\n'
        '💸 /withdraw - Withdraw funds\n'
        '🖼️ /upscale_image - Upscale an image\n'
        '🎥 /compress_video - Compress a video\n'
        '🤖 /ask_gpt - Ask GPT-4 a question\n'
        '🎵 /play_music - Play music\n'
        '🌦️ /weather - Get the current weather\n'
        '📰 /news - Get the latest news\n'
        '🌐 /translate - Translate text\n'
        '😂 /joke - Get a random joke\n'
        '👥 /group_menu - Show group menu'
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
    update.message.reply_text('Processing your image, please wait...')

# Define the message handler for upscaling images
def handle_upscale_image(update: Update, context: CallbackContext) -> None:
    photo = update.message.photo[-1].get_file()
    photo.download('image.jpg')
    img = Image.open('image.jpg')
    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)
    img.save('upscaled_image.jpg')
    update.message.reply_photo(photo=open('upscaled_image.jpg', 'rb'))

# Define the compress video command handler
def compress_video(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Processing your video, please wait...')

# Define the message handler for compressing videos
def handle_compress_video(update: Update, context: CallbackContext) -> None:
    video = update.message.video.get_file()
    video.download('video.mp4')
    clip = VideoFileClip('video.mp4')
    clip_resized = clip.resize(height=360)
    clip_resized.write_videofile('compressed_video.mp4', codec='libx264', audio_codec='aac')
    update.message.reply_text('Video compression complete.')
    update.message.reply_video(video=open('compressed_video.mp4', 'rb'))

# Define the play music command handler
def play_music(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please send the music file you want to play.')

# Define the message handler for playing music files
def handle_play_music(update: Update, context: CallbackContext) -> None:
    audio = update.message.audio.get_file()
    audio.download('music.mp3')
    update.message.reply_audio(audio=open('music.mp3', 'rb'))

# Define the weather command handler
def weather(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please send the location for which you want to get the weather.')

# Define the message handler for getting weather
def handle_weather(update: Update, context: CallbackContext) -> None:
    location = update.message.text
    api_key = os.getenv('WEATHER_API_KEY')
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric'
    response = requests.get(url).json()
    if response['cod'] == 200:
        weather_description = response['weather'][0]['description']
        temperature = response['main']['temp']
        update.message.reply_text(f'The weather in {location} is currently {weather_description} with a temperature of {temperature}°C.')
    else:
        update.message.reply_text('Could not retrieve weather data. Please check the location and try again.')

# Define the news command handler
def news(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Fetching the latest news headlines...')

# Define the message handler for getting news
def handle_news(update: Update, context: CallbackContext) -> None:
    api_key = os.getenv('NEWS_API_KEY')
    url = f'https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}'
    response = requests.get(url).json()
    if response['status'] == 'ok':
        headlines = [article['title'] for article in response['articles'][:5]]
        update.message.reply_text('\n'.join(headlines))
    else:
        update.message.reply_text('Could not retrieve news. Please try again later.')

# Define the translate command handler
def translate(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Please send the text you want to translate followed by the target language code (e.g., "Hello, world! es").')

# Define the message handler for translating text
def handle_translate(update: Update, context: CallbackContext) -> None:
    try:
        text, target_language = update.message.text.rsplit(' ', 1)
        api_key = os.getenv('TRANSLATE_API_KEY')
        url = f'https://translation.googleapis.com/language/translate/v2?key={api_key}'
        data = {'q': text, 'target': target_language}
        response = requests.post(url, data=data).json()
        translated_text = response['data']['translations'][0]['translatedText']
        update.message.reply_text(translated_text)
    except Exception as e:
        update.message.reply_text(f'Error: {str(e)}')

# Define the joke command handler
def joke(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Fetching a random joke...')

# Define the message handler for getting a joke
def handle_joke(update: Update, context: CallbackContext) -> None:
    url = 'https://official-joke-api.appspot.com/random_joke'
    response = requests.get(url).json()
    joke = f"{response['setup']} - {response['punchline']}"
    update.message.reply_text(joke)

# Define the tag command handler
def tag(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    members = bot.get_chat_administrators(chat_id)
    tags = " ".join([f"@{member.user.username}" for member in members if member.user.username])
    if tags:
        update.message.reply_text(f"Attention: {tags}")
    else:
        update.message.reply_text("No members with usernames found to tag.")

# Define the mute command handler
def mute(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    bot.restrict_chat_member(chat_id, update.message.reply_to_message.from_user.id, ChatPermissions(can_send_messages=False))
    update.message.reply_text('User has been muted.')

# Define the antilink command handler
def antilink(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Antilink functionality is not implemented yet.')

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
    elif query.data == 'upscale_image':
        upscale_image(query, context)
    elif query.data == 'compress_video':
        compress_video(query, context)
    elif query.data == 'ask_gpt':
        ask(query, context)
    elif query.data == 'play_music':
        play_music(query, context)
    elif query.data == 'group_menu':
        group_menu(query, context)
    elif query.data == 'tag':
        tag(query, context)
    elif query.data == 'mute':
        mute(query, context)
    elif query.data == 'antilink':
        antilink(query, context)
    elif query.data == 'weather':
        weather(query, context)
    elif query.data == 'news':
        news(query, context)
    elif query.data == 'translate':
        translate(query, context)
    elif query.data == 'joke':
        joke(query, context)

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
dispatcher.add_handler(CommandHandler("ask_gpt", ask))
dispatcher.add_handler(CommandHandler("upscale_image", upscale_image))
dispatcher.add_handler(CommandHandler("compress_video", compress_video))
dispatcher.add_handler(CommandHandler("play_music", play_music))
dispatcher.add_handler(CommandHandler("weather", weather))
dispatcher.add_handler(CommandHandler("news", news))
dispatcher.add_handler(CommandHandler("translate", translate))
dispatcher.add_handler(CommandHandler("joke", joke))
dispatcher.add_handler(CommandHandler("tag", tag))
dispatcher.add_handler(CommandHandler("mute", mute))
dispatcher.add_handler(CommandHandler("antilink", antilink))
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_withdraw))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_ask))
dispatcher.add_handler(MessageHandler(Filters.photo & ~Filters.command, handle_upscale_image))
dispatcher.add_handler(MessageHandler(Filters.video & ~Filters.command, handle_compress_video))
dispatcher.add_handler(MessageHandler(Filters.audio & ~Filters.command, handle_play_music))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_weather))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_news))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_translate))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_joke))

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
