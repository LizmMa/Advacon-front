from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen
from plyer import filechooser
from plyer import camera
import requests
from io import BytesIO
from PIL import Image as PILImage, ExifTags
import os
from kivy.clock import Clock
from kivy.uix.progressbar import ProgressBar
from functools import partial
from kivy.uix.image import AsyncImage
import re

# Устанавливаем размер окна приложения
Window.size = (412, 917)

# Путь сохранения текущего фото
PHOTO_PATH = 'latest_photo.jpg'

def correct_image_orientation(image_path):
    try:
        with PILImage.open(image_path) as img:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation, None)
                if orientation_value == 3:
                    img = img.rotate(180, expand=True)
                elif orientation_value == 6:
                    img = img.rotate(270, expand=True)
                elif orientation_value == 8:
                    img = img.rotate(90, expand=True)
                img.save(image_path)
    except Exception as e:
        print(f"Ошибка корректировки ориентации фото: {e}")

# Логика отправки фотографии на сервер и получения данных
def send_photo_to_server(filepath):
    try:
        with PILImage.open(filepath) as img:
            max_dimension = 1024
            img.thumbnail((max_dimension, max_dimension))  # пропорциональное уменьшение

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            compressed_image_bytes = buffer.getvalue()

            if len(compressed_image_bytes) > 2_000_000:
                print("Размер сжатого изображения все еще слишком большой")
                return None

        files = {'image': ('latest_photo.jpg', compressed_image_bytes, 'image/jpeg')}
        server_url = "http://185.12.94.106:8000/api/v1/images"
        response = requests.post(server_url, files=files)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Ошибка отправки на сервер: статус {response.status_code}, ответ: {response.text}")
            return None

    except Exception as ex:
        print(f"Ошибка при обработке фотографии: {ex}")
        return None

# Первый экран
class StartScreen(Screen):
    def __init__(self, **kwargs):
        super(StartScreen, self).__init__(**kwargs)
        layout = FloatLayout()

        # Фоновое изображение
        background_image = Image(
            source='фон_прозрачность.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
        )
        layout.add_widget(background_image)

        # Заголовок
        title = Label(
            text='Advacon',
            font_name='Jost/Jost.ttf',
            font_size=120,
            bold=True,
            color=(79/255, 23/255, 105/255, 0.8),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.9},
            size_hint=(None, None),
            size=(Window.width, 100)
        )
        layout.add_widget(title)

        # Описание
        description = Label(
            text='Определение характеристик\nсостояний зелёных насаждений города\nпо фото',
            font_name='Jost/Jost.ttf',
            font_size=40,
            bold=True,
            color=(79/255, 23/255, 105/255, 0.8),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.77},
            size_hint=(None, None),
            size=(412, 100)
        )
        layout.add_widget(description)

        # Кнопка "Сделать фото"
        button1 = Button(
            text='Сделать фото',
            bold=True,
            color=(0, 0, 0, 0.7),
            font_name='Jost/Jost.ttf',
            font_size=45,
            size_hint=(None, None),
            size=(470, 170),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            background_color=(2.5, 2.5, 2.5, 1)
        )
        button1.bind(on_release=self.capture_photo)
        layout.add_widget(button1)

        # Кнопка "Загрузить фото"
        button2 = Button(
            text='Загрузить фото',
            bold=True,
            color=(0, 0, 0, 0.7),
            font_name='Jost/Jost.ttf',
            font_size=45,
            size_hint=(None, None),
            size=(470, 170),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.28},
            background_color=(2.5, 2.5, 2.5, 1)
        )
        button2.bind(on_release=self.open_finder)
        layout.add_widget(button2)

        self.add_widget(layout)

    def capture_photo(self, instance):
        try:
            def on_photo_taken(path):
                if path:
                    correct_image_orientation(path)
                    self.manager.current = 'second_screen'
                    print("Фото сделано и сохранено.")
                    self.manager.get_screen('second_screen').load_photo(path)
                else:
                    print("Не удалось сделать фото")
            camera.take_picture(filename=PHOTO_PATH, on_complete=on_photo_taken)
        except Exception:
            pass

    def open_finder(self, instance):
        filechooser.open_file(on_selection=self.file_selected_callback)

    def file_selected_callback(self, selection):
        if selection:
            selected_path = selection[0]
            try:
                from shutil import copyfile
                copyfile(selected_path, PHOTO_PATH)
                correct_image_orientation(PHOTO_PATH)
                print(f"Фото выбрано и сохранено: {PHOTO_PATH}")
                self.manager.current = 'second_screen'
                self.manager.get_screen('second_screen').load_photo(PHOTO_PATH)
            except Exception as e:
                print(f"Ошибка при копировании файла: {e}")
        else:
            print("Фото не выбрано")

# Второй экран с отображением фотографии и кнопкой "Получить характеристики"
class SecondScreen(Screen):
    def __init__(self, **kwargs):
        super(SecondScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()

        # Фон
        background_image = Image(
            source='фон_прозрачность.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
        )
        self.layout.add_widget(background_image)

        # Заголовок
        title = Label(
            text='Advacon',
            font_name='Jost/Jost.ttf',
            font_size=120,
            bold=True,
            color=(79 / 255, 23 / 255, 105 / 255, 0.8),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.9},
            size_hint=(None, None),
            size=(Window.width, 100)
        )
        self.layout.add_widget(title)

        # Описание
        description = Label(
            text='Определение характеристик\nсостояний зелёных насаждений города\nпо фото',
            font_name='Jost/Jost.ttf',
            font_size=40,
            bold=True,
            color=(79 / 255, 23 / 255, 105 / 255, 0.8),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.77},
            size_hint=(None, None),
            size=(412, 100)
        )
        self.layout.add_widget(description)

        # Квадрат для фото (700x700, центр)
        self.square_pos = ((Window.width - 1475) / 2, (Window.height - 450) / 2)
        with self.layout.canvas:
            Color(rgb=(0.8, 0.8, 0.8))
            self.rect = Rectangle(pos=self.square_pos, size=(700, 700))

        # Виджет для отображения фото
        self.image_widget = Image(
            source=PHOTO_PATH,
            size=(700, 700),
            pos=self.square_pos,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(None,None),
        )
        self.layout.add_widget(self.image_widget)

        # Кнопка "Получить характеристики"
        button3 = Button(
            text='Получить характеристики',
            bold=True,
            color=(0, 0, 0, 0.7),
            font_name='Jost/Jost.ttf',
            font_size=37,
            size_hint=(None, None),
            size=(470, 170),
            halign='center',
            valign='top',
            pos_hint={'center_x': 0.5, 'center_y': 0.1},
            background_color=(2.5, 2.5, 2.5, 1)
        )
        button3.bind(on_release=self.send_photo_and_switch)
        self.layout.add_widget(button3)

        self.add_widget(self.layout)

        self.status_check_thread = None

    def load_photo(self, photo_path):
        if os.path.exists(photo_path):
            self.image_widget.source = photo_path
            self.image_widget.size = (700, 700)
            self.image_widget.size_hint = (None, None)
            self.image_widget.pos = self.square_pos
            self.image_widget.allow_stretch = True
            self.image_widget.keep_ratio = True
            self.image_widget.reload()
        else:
            print("Фотография не найдена для загрузки")

        self.progress_bar = ProgressBar(max=100, value=0, size_hint=(0.8, None), height=20,
                                        pos_hint={'center_x': 0.5, 'y': 0.03})
        self.layout.add_widget(self.progress_bar)

        self.progress_event = None

    def start_progress_animation(self):
        self.progress_bar.value = 0
        self.progress_event = Clock.schedule_interval(self.update_progress_bar, 0.05)


    def update_progress_bar(self, dt):
        if self.progress_bar.value >= 100:
            self.progress_bar.value = 0
        else:
            self.progress_bar.value += 1


    def stop_progress_animation(self):
        if self.progress_event:
            self.progress_event.cancel()
            self.progress_event = None
        self.progress_bar.value = 0

    def send_photo_and_switch(self, instance):
        print("Отправляю фото на сервер для анализа...")
        self.start_progress_animation()  # Запускаем анимацию прогресса

        response_data = send_photo_to_server(PHOTO_PATH)
        print("Получены характеристики:", response_data)
        if response_data and 'status' in response_data and response_data['status'] == 'uploaded':
            status_url = response_data.get('url')
            if status_url:
                print(f"Начинаю проверку статуса обработки по URL: {status_url}")
                self.status_event = Clock.schedule_interval(partial(self.check_status_and_update, status_url), 5)
            else:
                print("URL для проверки статуса не найден")
        else:
            print("Ошибка при получении характеристики или неподдерживаемый статус")

    def check_status_and_update(self, status_url, dt):
        try:
            response = requests.get(status_url)
            if response.status_code == 200:
                data = response.json()
                print(f"Проверка статуса: {data.get('status')}")
                if data.get('status') == 'failed':
                    if hasattr(self, 'status_event'):
                        self.status_event.cancel()
                    self.stop_progress_animation()
                    return False
                if data.get('status') in ['completed', 'done']:
                    if hasattr(self, 'status_event'):
                        self.status_event.cancel()
                    self.stop_progress_animation()

                    # Извлекаем ID из status_url
                    match = re.search(r'/api/v1/images/([a-f0-9\-]+)/status', status_url)
                    if not match:
                        print("Не удалось извлечь ID из URL статуса")
                        return False

                    image_id = match.group(1)
                    result_url = f"http://185.12.94.106:8000/api/v1/images/{image_id}/result"
                    print(f"Запрашиваем результаты по URL: {result_url}")

                    result_response = requests.get(result_url)
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        third_screen = self.manager.get_screen('third_screen')
                        third_screen.update_content(PHOTO_PATH, result_data)
                        self.manager.current = 'third_screen'
                    else:
                        print(f"Ошибка при запросе результатов: {result_response.status_code}")
                    return False
            else:
                print(f"Ошибка запроса статуса: {response.status_code}")
        except Exception as e:
            print(f"Ошибка при проверке статуса: {e}")
        return True

# Третий экран с результатами
class ThirdScreen(Screen):
    def __init__(self, **kwargs):
        super(ThirdScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()

        # Фон
        background_image = Image(
            source='фон_прозрачность.png',
            allow_stretch=True,
            keep_ratio=False,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
        )
        self.layout.add_widget(background_image)

        # Заголовок
        title = Label(
            text='Advacon',
            font_name='Jost/Jost.ttf',
            font_size=120,
            bold=True,
            color=(79 / 255, 23 / 255, 105 / 255, 0.8),
            halign='center',
            valign='middle',
            pos_hint={'center_x': 0.5, 'center_y': 0.9},
            size_hint=(None, None),
            size=(Window.width, 100)
        )
        self.layout.add_widget(title)

        # Квадрат под изображение результата (650x650, центр по X и Y)
        self.img_pos = ((Window.width - 1410) / 2, (Window.height + 600) / 2)
        with self.layout.canvas:
            Color(rgb=(0.8, 0.8, 0.8))
            self.rect = Rectangle(pos=self.img_pos, size=(650, 650))

        # Виджет для результата фотографии
        self.result_image = AsyncImage(
            source=PHOTO_PATH,
            size=(650, 650),
            pos=self.img_pos,
            allow_stretch=True,
            keep_ratio=True,
            size_hint=(None,None),
        )
        self.layout.add_widget(self.result_image)

        # Прокручиваемая таблица
        self.scroll_view = ScrollView(
            size_hint=(None, None),
            size=(700, 650),
            pos_hint={'center_x': 0.52, 'center_y': 0.32}
        )
        self.grid_table = GridLayout(cols=2, row_default_height=70, size_hint_y=None, spacing=(10, 20))
        self.grid_table.bind(minimum_height=self.grid_table.setter('height'))
        self.grid_table.cols_minimum = {0: 180, 1: 500}
        self.scroll_view.add_widget(self.grid_table)
        self.layout.add_widget(self.scroll_view)

        # Кнопка "Продолжить работу"
        button_continue = Button(
            text='Продолжить работу',
            bold=True,
            color=(0, 0, 0, 0.7),
            font_name='Jost/Jost.ttf',
            font_size=37,
            size_hint=(None, None),
            size=(370, 110),
            halign='center',
            valign='top',
            pos_hint={'center_x': 0.5, 'center_y': 0.055},
            background_color=(2.5, 2.5, 2.5, 1)
        )
        button_continue.bind(on_release=self.return_to_start_screen)
        self.layout.add_widget(button_continue)

        self.add_widget(self.layout)

    def update_content(self, photo_path, characteristics):
        img_url = characteristics.get('imgUrl', photo_path)
        self.result_image.source = img_url

        self.result_image.size = (650, 650)
        self.result_image.size_hint = (None, None)
        self.result_image.pos = self.img_pos
        self.result_image.allow_stretch = True
        self.result_image.keep_ratio = True
        self.result_image.reload()

        self.grid_table.clear_widgets()

        headers = ["Объект", "Описание характеристик \n по фотографиям"]
        for header in headers:
            lbl = Label(
                text=header,
                bold=True,
                font_size=36,
                color=(0, 0, 0, 0.7),
                halign='center',
                valign='middle',
            )
            lbl.text_size = (self.grid_table.cols_minimum[headers.index(header)], None)
            self.grid_table.add_widget(lbl)

        results = characteristics.get('result', [])
        for result_str in results:
            # Ищем первое число и разбиваем строку на две части по этому числу и пробелу после него
            match = re.search(r'(\d+(\.\d+)?)(.*)', result_str)
            if match:
                first_part_end = match.end(1)
                part1 = result_str[:first_part_end]
                part2 = result_str[first_part_end:].strip()
            else:
                part1 = result_str
                part2 = ""

            label1 = Label(
                text=part1,
                font_size=30,
                color=(0, 0, 0, 0.7),
                halign='center',
                valign='middle',
                text_size=(self.grid_table.cols_minimum[0], None)
            )
            label2 = Label(
                text=part2,
                font_size=30,
                color=(0, 0, 0, 0.7),
                halign='center',
                valign='middle',
                text_size=(self.grid_table.cols_minimum[1], None)
            )
            self.grid_table.add_widget(label1)
            self.grid_table.add_widget(label2)

    def return_to_start_screen(self, instance):
        self.manager.current = 'start_screen'

# Главный класс приложения
class AdvaconApp(App):
    def build(self):
        screen_manager = ScreenManager()
        screen_manager.add_widget(StartScreen(name='start_screen'))
        screen_manager.add_widget(SecondScreen(name='second_screen'))
        screen_manager.add_widget(ThirdScreen(name='third_screen'))
        return screen_manager

if __name__ == '__main__':
    AdvaconApp().run()