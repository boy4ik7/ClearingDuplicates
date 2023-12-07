from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.clock import Clock
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from copy import copy
import os
import platform
import hashlib
import asyncio

os_info = platform.system()
screen_manager = ScreenManager()
duplicate_files_by_hash = []
delete_list = []
delete_list_complite = []
directory_select = None
percent_scan = None
flag = False

class ScanPopup(Popup):
    def __init__(self, **kwargs):
        super(ScanPopup, self).__init__(**kwargs)
        self.title = 'Прогрес'
        layout = BoxLayout(orientation='vertical')
        self.label = Label(text='Подождите...')
        layout.add_widget(self.label)
        buttons_layout = BoxLayout(size_hint_y=None, height=50)
        layout.add_widget(buttons_layout)
        cancel_button = Button(text='Отмена')
        cancel_button.bind(on_release=self.cancel)
        buttons_layout.add_widget(cancel_button)
        self.content = layout
        Clock.schedule_interval(self.update_percent, 1)
        self.task = None
    
    async def get_duplicate_files_by_hash(self, directory):
        files_by_hash = {}
        files_list = os.listdir(directory)
        file_count = len(files_list)
        counter = 0
        for dirpath, _, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                with open(filepath, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash in files_by_hash:
                    files_by_hash[file_hash].append((filepath, filename))
                else:
                    files_by_hash[file_hash] = [(filepath, filename)]
                counter += 1
                global percent_scan
                percent_scan = int((counter / file_count) * 100)
                #print(f"Обработка: {percent_scan}%")
        duplicate_files = {hash_value: file_info for hash_value, file_info in files_by_hash.items() if len(file_info) > 1}
        global duplicate_files_by_hash
        for key, value in duplicate_files.items():
            for file_path_tuple in value:
                name = file_path_tuple[1]
                patch = file_path_tuple[0]
                duplicate_files_by_hash.append({"name": name, "checked": False, "patch": patch})
        #print(duplicate_files_by_hash)
        percent_scan = "done"
        #print("Готово.")

    def start_task(self, directory):
        return asyncio.create_task(self.get_duplicate_files_by_hash(directory))

    def cancel(self, instance):
        if self.task:
            self.task.cancel()
        self.dismiss()
    
    def update_percent(self, dt):
        global percent_scan
        if percent_scan == "done":
            self.label.text = "Готово"
            #self.percent = 0
            percent_scan = None
            self.dismiss()
            second_screen = SecondScreen(name='second', category_data=duplicate_files_by_hash) #category_data
            screen_manager.add_widget(second_screen)
            screen_manager.current = 'second'
        else:
            self.label.text = f'{percent_scan}%' 

class DirectoryChooserPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Выбор пути'
        self.size_hint = (0.8, 0.6)
        content_layout = BoxLayout(orientation='vertical')
        self.text_input = TextInput(text=os.getcwd(), multiline=False)
        content_layout.add_widget(self.text_input)
        buttons_layout = BoxLayout(size_hint_y=0.2)
        content_layout.add_widget(buttons_layout)
        self.ok_button = Button(text='OK')
        self.ok_button.bind(on_release=self.dismiss_popup)
        buttons_layout.add_widget(self.ok_button)
        self.cancel_button = Button(text='Отмена')
        self.cancel_button.bind(on_release=self.dismiss)
        buttons_layout.add_widget(self.cancel_button)
        self.content = content_layout
    
    def dismiss_popup(self, instance):
        chosen_directory = self.text_input.text
        
        async def open_scan_popup():
            if os.path.isdir(chosen_directory):
                #print(f"Выбрана директория: {chosen_directory}")
                global directory_select
                directory_select = chosen_directory
                self.dismiss()
                popup = ScanPopup()
                await popup.start_task(chosen_directory)
                popup.open()
            else:
                #print(f"Указанный путь не является директорией: {chosen_directory}")
                error_popup = ErrorPopup(message=f"Указанный путь не является директорией: {chosen_directory}")
                error_popup.open()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(open_scan_popup())
        loop.close()  

class ErrorPopup(Popup):
    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Ошибка'
        self.size_hint = (0.5, 0.5)
        content_layout = BoxLayout(orientation='vertical')
        self.error_label = Label(text=message)
        content_layout.add_widget(self.error_label)
        ok_button = Button(text='OK')
        ok_button.bind(on_release=self.dismiss)
        content_layout.add_widget(ok_button)
        self.content = content_layout

class FirstScreen(Screen):
    def __init__(self, **kwargs):
        super(FirstScreen, self).__init__(**kwargs)

    def on_enter(self):
        layout = BoxLayout(orientation='vertical')

        file_chooser = FileChooserListView(path='/', dirselect=True)

        def selected(instance, selection):
            if selection:
                chosen_directory = selection[0]
                async def open_scan_popup():
                    if os.path.isdir(chosen_directory):
                        #print(f"Выбрана директория: {chosen_directory}")
                        global directory_select
                        directory_select = chosen_directory
                        popup = ScanPopup()
                        await popup.start_task(chosen_directory)
                        popup.open()
                    else:
                        #print(f"Указанный путь не является директорией: {chosen_directory}")
                        error_popup = ErrorPopup(message=f"Указанный путь не является директорией: {chosen_directory}")
                        error_popup.open()

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(open_scan_popup())
                loop.close()

        def select_folder(instance):
            if file_chooser.selection:
                selected(file_chooser, file_chooser.selection)

        def input_selection(instance):
            popup = DirectoryChooserPopup()
            popup.open()

        def cancel_selection(instance):
            file_chooser.selection = []
            file_chooser.path = '/'

        def quit_selection(instance):
            App.get_running_app().stop()

        select_button = Button(text='Выбрать папку', size_hint=(1, None), height=50)
        select_button.bind(on_release=select_folder)
        layout.add_widget(select_button)

        cancel_button = Button(text='Домой', size_hint=(1, None), height=50)
        cancel_button.bind(on_release=cancel_selection)
        layout.add_widget(cancel_button)

        if os_info == "Windows" or os_info == "Linux":
            input_button = Button(text='Ввести путь вручную', size_hint=(1, None), height=50, background_color=(0, 0.9, 0, 1))
            input_button.bind(on_release=input_selection)
            layout.add_widget(input_button)
        else:
            quit_button = Button(text='Выход', size_hint=(1, None), height=50, background_color=(0.4, 0.5, 1, 1))
            quit_button.bind(on_release=quit_selection)
            layout.add_widget(quit_button)

        layout.add_widget(file_chooser)

        self.add_widget(layout)

class ConfirmationPopup(Popup):
    def __init__(self, delete_list, **kwargs):
        super().__init__(**kwargs)
        self.len = len(delete_list)
        if self.len > 0:
            self.title = 'Подтверждение. Выбранные файлы будут удалены безвозвратно'
            self.size_hint = (0.8, 0.8)
        else:
            self.title = 'Подтверждение'
            self.size_hint = (0.8, 0.3)
        self.list = "\n".join(delete_list)
        content_layout = BoxLayout(orientation='vertical')
        if self.len > 0:
            self.error_label = Label(text=f"Вы уверены что хотите удалить: \n{self.list}\n?", size_hint_y=None)
            self.error_label.bind(size=self.error_label.setter('text_size'))
            self.error_label.bind(texture_size=lambda instance, size: setattr(self.error_label, 'height', size[1]))
            
            scroll_view = ScrollView(size_hint=(1, 1), size=(self.width, self.height * 0.6))
            scroll_view.add_widget(self.error_label)
            content_layout.add_widget(scroll_view)
        else:
            self.error_label = Label(text=f"Выберите хотя бы один элемент")
            content_layout.add_widget(self.error_label)
        if self.len > 0:
            yes_button = Button(text='Да', size_hint=(1, 0.1), background_color=(2, 0, 0, 1))
            yes_button.bind(on_release=self.delete_file)
            content_layout.add_widget(yes_button)
            cancel_button = Button(text='Нет', size_hint=(1, 0.1))
            cancel_button.bind(on_release=self.dismiss)
            content_layout.add_widget(cancel_button)
        else:
            ok_button = Button(text='Ок', size_hint=(1, 0.5))
            ok_button.bind(on_release=self.dismiss)
            content_layout.add_widget(ok_button)
        self.content = content_layout

    def delete_file(self, file_list):
        #print(f"Переходим к удалению {delete_list}")
        self.dismiss()
        error_popup = DeletePopup()
        error_popup.open()

class DeletePopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Удаляем'
        self.size_hint = (0.5, 0.5)
        self.auto_dismiss = False
        self.error_label = Label(text="Подождите...")
        content_layout = BoxLayout(orientation='vertical')
        content_layout.add_widget(self.error_label)
        self.content = content_layout
        self.sum = len(delete_list)
        self.counter = 0
        self.percent = None
        global delete_list_complite
        delete_list_complite = copy(delete_list)
        Clock.schedule_interval(self.update_counter, 1)

    def update_counter(self, dt):
        global delete_list_complite
        if delete_list:
            error = False
            file_to_delete = delete_list[0]
            if os.path.exists(file_to_delete):
                os.remove(file_to_delete)
                #print(f"Файл {file_to_delete} удален.")
                del delete_list[0]
                #print(f"Путь {file_to_delete} удален из списка.")
            else:
                del delete_list[0]
                #print(f"Файл {file_to_delete} не существует.")
                error = True
            self.counter = self.sum - len(delete_list)
            self.percent = int((self.counter / self.sum) * 100)
            if error is True:
                self.error_label.text = f"Ошибка удаления {file_to_delete}, пропускаем..."  
            else:
                self.error_label.text = f"Подождите... {self.percent}%"    
        else:
            self.dismiss()
            Clock.schedule_once(self.open_quit, 0.1)
    
    def open_quit(self, dt):
        if not hasattr(self, 'quit_popup_opened') or not self.quit_popup_opened:
            self.quit_popup_opened = True
            quit_popup = QuitPopup()
            quit_popup.open()

class QuitPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.auto_dismiss = False
        self.title = 'Готово'
        self.size_hint = (0.8, 0.8)
        self.list = "\n".join(delete_list_complite)
        content_layout = BoxLayout(orientation='vertical')
        self.error_label = Label(text=f"Файлы: \n{self.list}\nудалены.", size_hint_y=None)
        self.error_label.bind(size=self.error_label.setter('text_size'))
        self.error_label.bind(texture_size=lambda instance, size: setattr(self.error_label, 'height', size[1]))  
        scroll_view = ScrollView(size_hint=(1, 1), size=(self.width, self.height * 0.6))
        scroll_view.add_widget(self.error_label)
        content_layout.add_widget(scroll_view)
        quit_button = Button(text='Выйти', size_hint=(1, 0.1), background_color=(0.4, 0.5, 1, 1))
        quit_button.bind(on_release=self.quit_app)
        content_layout.add_widget(quit_button)
        self.content = content_layout

    def quit_app(self, quit):
        App.get_running_app().stop()

class SecondScreen(Screen):
    def __init__(self, category_data, **kwargs):
        super(SecondScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')

        scroll_layout = GridLayout(cols=3, spacing=100, size_hint_y=None, padding=20)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))
        global duplicate_files_by_hash
        for item in duplicate_files_by_hash:#items:
            image = Image(source=item["patch"], size_hint=(None, None), size=(200, 200))
            label = Label(text=item["name"], font_size='20sp', halign='center', valign='middle', padding=(20, 0))
            checkbox = CheckBox(active=item["checked"], size_hint=(None, 50), size=(50, 50))
            checkbox.label_name = label.text  # Сохраняем текст Label в CheckBox
            checkbox.label_patch = item["patch"]
            checkbox.bind(active=self.on_checkbox_active)
            scroll_layout.add_widget(image)
            scroll_layout.add_widget(label)
            scroll_layout.add_widget(checkbox)

        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_view.add_widget(scroll_layout)
        layout.add_widget(scroll_view)
        buttons_layout = GridLayout(cols=2, size_hint=(1, None), height=50)
        quit_button = Button(text='Выйти', size_hint=(0.3, 1), background_color=(0.4, 0.5, 1, 1))
        quit_button.bind(on_release=self.quit_app)
        buttons_layout.add_widget(quit_button)
        delete_button = Button(text='Удалить', size_hint=(0.7, 1), background_color=(2, 0, 0, 1))
        delete_button.bind(on_release=self.delete_files)
        buttons_layout.add_widget(delete_button)
        layout.add_widget(buttons_layout)
        self.add_widget(layout)
        
    def delete_files(self, delete):
        error_popup = ConfirmationPopup(delete_list=delete_list)
        error_popup.open()

    def quit_app(self, quit):
        App.get_running_app().stop()

    def on_checkbox_active(self, checkbox, value):
        if value:
            delete_list.append(checkbox.label_patch)
            #print(f"Checked: {checkbox.label_patch}, {checkbox.label_name}")
            #print(delete_list)
        else:
            delete_list.remove(checkbox.label_patch)
            #print(f"Unchecked: {checkbox.label_patch}, {checkbox.label_name}")
            #print(delete_list)
        
    
    def delete_files(self, delete):
        error_popup = ConfirmationPopup(delete_list=delete_list)
        error_popup.open()

    def quit_app(self, quit):
        App.get_running_app().stop()

    def on_checkbox_active(self, checkbox, value):
        if value:
            delete_list.append(checkbox.label_patch)
            #print(f"Checked: {checkbox.label_patch}, {checkbox.label_name}")
            #print(delete_list)
        else:
            delete_list.remove(checkbox.label_patch)
            #print(f"Unchecked: {checkbox.label_patch}, {checkbox.label_name}")
            #print(delete_list)

class MyApp(App):
    def build(self):
        first_screen = FirstScreen(name='first')
        screen_manager.add_widget(first_screen)
        return screen_manager

if __name__ == '__main__':
    MyApp().run()
