import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
from connect import *  #підключення до бази даних
from telegram.ext import Filters



if not os.path.exists('voice_messages'):
    os.makedirs('voice_messages')



client = client
db = client['voice_messages']
collection = db['messages']



def save_voice_message(update: Update, context: CallbackContext):

    if not os.path.exists('voice_messages'):
        os.makedirs('voice_messages')

    voice_message = update.message.voice
    file_id = voice_message.file_id
    user_id = update.message.from_user.id


    file = context.bot.get_file(file_id)
    file.download(f'voice_messages/{user_id}_{file_id}.ogg')


    collection.insert_one({
        'user_id': user_id,
        'file_id': file_id,
        'file_path': f'voice_messages/{user_id}_{file_id}.ogg'
    })


def start(update: Update, context: CallbackContext):
    update.message.reply_text('Привіт! Я готовий обробляти голосові повідомлення.')

def main():

    token = TOKEN


    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.voice, save_voice_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
