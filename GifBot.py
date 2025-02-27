import telebot
import os
import ffmpeg
from telebot import types
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import imageio
import imageio_ffmpeg  # Ensure ffmpeg plugin is loaded
import numpy as np  # Import numpy

# Вставьте токен вашего бота
TOKEN = '7574291610:AAHNAHvo9ZOb_D6mfumK9anvztIwewXZ-qc'
bot = telebot.TeleBot(TOKEN)

# Путь для сохранения видео и GIF
VIDEO_PATH = "input_video.mp4"
GIF_PATH = "output.gif"

# Обработчик для видео
@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        if not message.video:
            raise ValueError("Видео не было отправлено.")
        
        # Получаем файл видео
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем видео на диск (перезаписываем)
        with open(VIDEO_PATH, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # Отправляем пользователю меню с возможностями
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Преобразовать в GIF", "Добавить текст", "Повернуть/Отразить", "Обрезать", "Изменить FPS", "Обратный GIF", "Генерация стикеров", "Фильтры для видео")
        bot.send_message(message.chat.id, "Выберите операцию с видео или GIF", reply_markup=markup)

    except ValueError as ve:
        bot.reply_to(message, str(ve))
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я GifBot. Отправьте мне видео, и я помогу вам преобразовать его в GIF или выполнить другие операции.")
    
    # Отправляем пользователю меню с возможностями
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Преобразовать в GIF", "Добавить текст", "Повернуть/Отразить", "Обрезать", "Изменить FPS", "Обратный GIF", "Генерация стикеров", "Фильтры для видео")
    bot.send_message(message.chat.id, "Выберите операцию с видео или GIF", reply_markup=markup)

# Функция для конвертации видео в GIF с использованием ffmpeg-python
def convert_video_to_gif(input_video, output_gif, scale='320:-1', fps=15):
    try:
        (
            ffmpeg
            .input(input_video)
            .output(output_gif, vf=f'scale={scale}', r=fps)
            .run(overwrite_output=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print(e.stderr.decode('utf-8'))
        raise

# Обработчик команд выбора
@bot.message_handler(func=lambda message: True)
def handle_operations(message):
    if message.text == "Преобразовать в GIF":
        convert_video_to_gif(VIDEO_PATH, GIF_PATH)
        with open(GIF_PATH, 'rb') as gif_file:
            bot.send_animation(message.chat.id, gif_file)
    elif message.text == "Добавить текст":
        bot.send_message(message.chat.id, "Введите текст для добавления в GIF.")
        bot.register_next_step_handler(message, add_text)
    elif message.text == "Повернуть/Отразить":
        bot.send_message(message.chat.id, "Выберите действие: Повернуть или Отразить.")
        bot.register_next_step_handler(message, rotate_or_flip)
    elif message.text == "Обрезать":
        bot.send_message(message.chat.id, "Введите начало и конец обрезки (в секундах), например: 5 10.")
        bot.register_next_step_handler(message, crop_video)
    elif message.text == "Изменить FPS":
        bot.send_message(message.chat.id, "Введите новый FPS для GIF.")
        bot.register_next_step_handler(message, change_fps)
    elif message.text == "Обратный GIF":
        reversed_gif_path = reverse_gif(GIF_PATH)
        with open(reversed_gif_path, 'rb') as gif_file:
            bot.send_animation(message.chat.id, gif_file)
    elif message.text == "Генерация стикеров":
        generate_sticker(GIF_PATH, message.chat.id)
    elif message.text == "Фильтры для видео":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Сепия", "Черно-белый", "Размытие", "Резкость")
        bot.send_message(message.chat.id, "Выберите фильтр для применения к видео:", reply_markup=markup)
        bot.register_next_step_handler(message, apply_video_filter)

# Пример функций для каждого действия:

# Добавление текста
def add_text(message):
    text = message.text
    # Загружаем GIF
    gif_path = "output.gif"  # Путь к GIF
    img = Image.open(gif_path)

    # Применяем текст к каждому кадру GIF
    frames = []
    for frame in range(img.n_frames):
        img.seek(frame)
        frame_image = img.copy()
        draw = ImageDraw.Draw(frame_image)
        font = ImageFont.load_default()  # Используем стандартный шрифт

        # Получаем размеры изображения и текста
        width, height = frame_image.size
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Позиционируем текст в центре
        position = ((width - text_width) // 2, (height - text_height) // 2)

        # Добавляем текст на текущий кадр
        draw.text(position, text, font=font, fill=(255, 255, 255))

        # Добавляем кадр в список
        frames.append(frame_image)

    # Сохраняем изменённый GIF
    output_path = "output_with_text.gif"
    frames[0].save(output_path, save_all=True, append_images=frames[1:], loop=0)

    # Отправляем изменённый GIF обратно пользователю
    with open(output_path, 'rb') as gif_file:
        bot.send_animation(message.chat.id, gif_file)

    # Удаляем временный файл
    os.remove(output_path)
    bot.send_message(message.chat.id, "Текст добавлен.")
    
# Поворот или отражение
def rotate_or_flip(message):
    action = message.text
    gif_path = "output.gif"  # Путь к GIF

    # Открытие GIF файла
    img = Image.open(gif_path)

    # Вращение или отражение изображения в зависимости от команды пользователя
    if action == "Повернуть":
        # Поворот на 90 градусов
        img = img.rotate(90, expand=True)
    elif action == "Отразить":
        # Отражение по горизонтали
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    # Сохранение изменённого GIF
    output_path = "output_rotated_or_flipped.gif"
    img.save(output_path)

    # Отправка изменённого GIF обратно пользователю
    with open(output_path, 'rb') as gif_file:
        bot.send_animation(message.chat.id, gif_file)

    # Удаление временного файла
    os.remove(output_path)

    # Ответ пользователю
    bot.send_message(message.chat.id, f"Выполнено действие: {action}.")
    
# Обрезка видео
def crop_video(message):
    try:
        # Разбираем сообщение, чтобы получить начальную и конечную временные метки
        start, end = map(int, message.text.split())
        
        # Путь к исходному видео и к временным файлам
        input_video_path = VIDEO_PATH
        temp_video_path = "temp_video.mp4"
        
        # Используем ffmpeg для обрезки видео
        ffmpeg.input(input_video_path, ss=start, to=end).output(temp_video_path).run(overwrite_output=True, capture_stderr=True)
        
        # Перемещаем временный файл на место исходного
        os.replace(temp_video_path, input_video_path)
        
        # Отправляем пользователю обрезанное видео
        with open(input_video_path, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file)

        # Ответ пользователю
        bot.send_message(message.chat.id, f"Видео обрезано с {start} по {end} секунд.")

    except ffmpeg.Error as e:
        print(e.stderr.decode('utf-8'))
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
    
# Изменение FPS
def change_fps(message):
    try:
        # Получаем новое значение FPS от пользователя
        fps = int(message.text)
        
        # Путь к исходному GIF и к временным файлам
        input_gif_path = GIF_PATH
        temp_gif_path = "temp_output.gif"
        
        # Используем ffmpeg для изменения FPS
        ffmpeg.input(input_gif_path).output(temp_gif_path, r=fps).run(overwrite_output=True, capture_stderr=True)
        
        # Перемещаем временный файл на место исходного
        os.replace(temp_gif_path, input_gif_path)

        # Отправляем изменённый GIF обратно пользователю
        with open(input_gif_path, 'rb') as gif_file:
            bot.send_animation(message.chat.id, gif_file)

        # Ответ пользователю
        bot.send_message(message.chat.id, f"FPS изменен на {fps}.")

    except ffmpeg.Error as e:
        print(e.stderr.decode('utf-8'))
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
    
# Обратный GIF
def reverse_gif(input_gif):
    try:
        # Чтение исходного GIF
        gif = imageio.mimread(input_gif)

        # Инвертируем кадры
        reversed_gif = gif[::-1]

        # Сохраняем обратный GIF во временный файл
        temp_gif_path = "temp_output.gif"
        imageio.mimsave(temp_gif_path, reversed_gif)
        
        # Перемещаем временный файл на место исходного
        os.replace(temp_gif_path, input_gif)

        return input_gif
    except Exception as e:
        print(str(e))
        raise

# Генерация стикеров
def generate_sticker(gif_path, chat_id):
    try:
        # Путь к выходному стикеру в формате WebP
        sticker_path = "sticker.webp"
        
        # Преобразуем GIF в WebP с помощью ffmpeg
        ffmpeg.input(gif_path).output(sticker_path, vcodec='libwebp', loop=0, c='copy').run(overwrite_output=True)

        # Отправляем стикер пользователю
        with open(sticker_path, 'rb') as sticker_file:
            bot.send_sticker(chat_id, sticker_file)

        # Удаляем временный файл стикера
        os.remove(sticker_path)

    except Exception as e:
        bot.send_message(chat_id, f"Произошла ошибка при генерации стикера: {str(e)}")

# Применение фильтров к видео
def apply_video_filter(message):
    try:
        # Получаем тип фильтра из текста
        filter_type = message.text.lower()
        
        # Путь к исходному видео и к временным файлам
        input_video_path = VIDEO_PATH
        temp_video_path = "temp_video.mp4"
        
        # Применение фильтра в зависимости от типа
        if filter_type in ["sepia", "сепия"]:
            filter_str = "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
        elif filter_type in ["grayscale", "черно-белый"]:
            filter_str = "hue=s=0"
        elif filter_type in ["blur", "размытие"]:
            filter_str = "boxblur=10:10"
        elif filter_type in ["sharpen", "резкость"]:
            filter_str = "unsharp=5:5:1.0:5:5:0.0"
        else:
            bot.send_message(message.chat.id, f"Фильтр {filter_type} не распознан.")
            return
        
        # Используем ffmpeg для применения фильтра к видео
        ffmpeg.input(input_video_path).output(temp_video_path, vf=filter_str).run(overwrite_output=True, capture_stderr=True)
        
        # Перемещаем временный файл на место исходного
        os.replace(temp_video_path, input_video_path)
        
        # Отправляем пользователю видео с применённым фильтром
        with open(input_video_path, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file)

        # Ответ пользователю
        bot.send_message(message.chat.id, f"Фильтр {filter_type} применен к видео.")

        # Возвращаемся в основное меню
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Преобразовать в GIF", "Добавить текст", "Повернуть/Отразить", "Обрезать", "Изменить FPS", "Обратный GIF", "Генерация стикеров", "Фильтры для видео")
        bot.send_message(message.chat.id, "Выберите операцию с видео или GIF", reply_markup=markup)

    except ffmpeg.Error as e:
        print(e.stderr.decode('utf-8'))
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {str(e)}")

# Запуск бота
bot.polling()
