from pytube import YouTube, Playlist
from telegram.error import TimedOut
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import os
from pytube.exceptions import AgeRestrictedError
import threading

TOKEN = 'YOUR_TOKEN'
user_data = {}

def start(update, context):
    update.message.reply_text('Привет! Отправь мне ссылку на видео или плейлист с YouTube.')

def download_video(update, context):
    chat_id = update.message.chat_id
    url = update.message.text
    if 'playlist' in url:
        user_data[chat_id] = {'downloading': True, 'thread': None}
        user_data[chat_id]['thread'] = threading.Thread(target=download_playlist, args=(update, context, url, chat_id))
        user_data[chat_id]['thread'].start()
    else:
        download_single_video(update, context, url)

def download_single_video(update, context, url):
    try:
        yt = YouTube(url)
        video = yt.streams.filter(file_extension='mp4').first()
        download_path = video.download()
        update.message.reply_text('Видео загружено, отправляю...')
        update.message.reply_video(video=open(download_path, 'rb'))
        os.remove(download_path)
    except AgeRestrictedError:
        update.message.reply_text(
            'Произошла ошибка при попытке скачать видео. Возможно, видео имеет ограничения, которые мешают его загрузке.')
    except Exception as e:
        update.message.reply_text(f'Произошла ошибка при скачивании видео: {e}')
    except TimedOut as e:
        update.message.reply_text('Произошла ошибка: время ожидания истекло. Попробуйте ещё раз.')

def download_playlist(update, context, url, chat_id):
    try:
        pl = Playlist(url)
        total_videos = len(pl.video_urls)
        update.message.reply_text(f'Найден плейлист с {total_videos} видео. Начинаю загрузку...')
        successful_downloads = 0
        for index, video_url in enumerate(pl.video_urls, start=1):
            if not user_data.get(chat_id, {}).get('downloading'):
                update.message.reply_text(
                    f'Загрузка плейлиста остановлена. Успешно загружено {successful_downloads} из {total_videos} видео.')
                break
            try:
                download_and_send_video(video_url, update, context, chat_id)
                successful_downloads += 1
            except AgeRestrictedError:
                update.message.reply_text(
                    f'Видео {index} из {total_videos} имеет возрастные ограничения и будет пропущено.')
            except Exception as e:
                update.message.reply_text(f'Произошла ошибка при скачивании видео {index} из {total_videos}: {e}')
            update.message.reply_text(f'Прогресс: {index} из {total_videos} видео обработано.')
        if user_data.get(chat_id, {}).get('downloading'):
            update.message.reply_text(
                f'Все видео из плейлиста загружены и отправлены. Успешно загружено {successful_downloads} из {total_videos} видео.')
        user_data[chat_id]['downloading'] = False
    except Exception as e:
        update.message.reply_text(f'Произошла ошибка при скачивании плейлиста: {e}')
        user_data[chat_id]['downloading'] = False

def download_and_send_video(url, update, context, chat_id):
    try:
        yt = YouTube(url)
        video = yt.streams.filter(file_extension='mp4').first()
        file_size = video.filesize
        estimated_time = calculate_estimated_time(file_size)
        update.message.reply_text(f'Ожидаемое время загрузки видео: {estimated_time} секунд.')
        download_path = video.download()
        if user_data.get(chat_id, {}).get('downloading'):
            update.message.reply_text('Загрузка завершена! Отправляю видео...')
            update.message.reply_video(video=open(download_path, 'rb'))
        os.remove(download_path)
    except Exception as e:
        if 'download_path' in locals() and os.path.exists(download_path):
            os.remove(download_path)
        raise e

def calculate_estimated_time(file_size):
    average_download_speed = 500000
    estimated_time = file_size / average_download_speed
    return round(estimated_time)

def stop(update, context):
    chat_id = update.message.chat_id
    if chat_id in user_data:
        user_data[chat_id]['downloading'] = False
        update.message.reply_text('Загрузка будет остановлена.')
    else:
        update.message.reply_text('Нет активной загрузки для остановки.')

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
