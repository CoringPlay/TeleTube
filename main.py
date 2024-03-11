from pytube import YouTube
from telegram.error import TimedOut
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from pytube.exceptions import AgeRestrictedError

TOKEN = 'TELEGRAM_BOT_TOKEN'

def start(update, context):
    update.message.reply_text('Привет! Отправь мне ссылку на видео с YouTube.')

def download_video(update, context):
    url = update.message.text
    try:
        yt = YouTube(url)
        video = yt.streams.filter(file_extension='mp4').first()
        download_path = video.download()
        update.message.reply_text('Видео загружено, отправляю...')
        update.message.reply_video(video=open(download_path, 'rb'))
        os.remove(download_path)
    except AgeRestrictedError:
        update.message.reply_text('Произошла ошибка при попытке скачать видео. Возможно, видео имеет ограничения, которые мешают его загрузке.')
    except Exception as e:
        update.message.reply_text(f'Произошла ошибка при скачивании видео: {e}')
    except TimedOut as e:
        update.message.reply_text('Произошла ошибка: время ожидания истекло. Попробуйте ещё раз.')

def download_and_send_video(url, update, context):
    yt = YouTube(url)
    video = yt.streams.filter(file_extension='mp4').first()
    file_size = video.filesize
    estimated_time = calculate_estimated_time(file_size)
    update.message.reply_text(f'Ожидаемое время загрузки: {estimated_time} секунд.')
    download_path = video.download()
    update.message.reply_text('Загрузка завершена! Отправляю видео...')
    update.message.reply_video(video=open(download_path, 'rb'))
    os.remove(download_path)

def calculate_estimated_time(file_size):
    average_download_speed = 500000
    estimated_time = file_size / average_download_speed
    return round(estimated_time)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
