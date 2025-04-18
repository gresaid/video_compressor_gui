import dearpygui.dearpygui as dpg
from tkinter import filedialog, Tk


class CompressionView:
    def __init__(self, controller):
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        """Настраивает пользовательский интерфейс"""
        dpg.create_context()

        # Стили и шрифты
        with dpg.font_registry():
            # Здесь можно добавить пользовательские шрифты
            pass

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6, category=dpg.mvThemeCat_Core)

        dpg.bind_theme(global_theme)

        # Основное окно
        with dpg.window(label="Видео Компрессор", width=650, height=650, tag="main_window", no_resize=True):
            # Выбор папок
            with dpg.collapsing_header(label="Папки", default_open=True):
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Выберите входную папку", callback=self.on_select_input_folder)
                        dpg.add_text("Папка: не выбрана", tag="selected_folder")

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Выберите выходную папку", callback=self.on_select_output_folder)
                        dpg.add_text("Папка: не выбрана", tag="selected_output_folder")
                        dpg.add_checkbox(label="Та же, что и входная", default_value=True,
                                         callback=self.on_same_folder_toggle, tag="same_folder_checkbox")

            # Настройки файлов
            with dpg.collapsing_header(label="Настройки файлов", default_open=True):
                with dpg.group():
                    dpg.add_combo(
                        label="Формат входных файлов",
                        items=["mp4", "mkv", "avi", "mov", "webm"],
                        default_value="mp4",
                        callback=self.on_input_extension_changed,
                        width=200
                    )

                    dpg.add_combo(
                        label="Формат выходных файлов",
                        items=["mp4", "mkv", "avi", "mov", "webm"],
                        default_value="mp4",
                        callback=self.on_output_extension_changed,
                        width=200
                    )

            # Настройки кодирования
            with dpg.collapsing_header(label="Настройки кодирования", default_open=True):
                with dpg.group():
                    dpg.add_slider_int(
                        label="Количество потоков",
                        default_value=1,
                        min_value=1,
                        max_value=8,
                        callback=self.on_threads_changed,
                        width=250
                    )

                    dpg.add_combo(
                        label="Предустановка кодирования",
                        items=[
                            "Оригинальный (AV1 NVENC)",
                            "Высокое качество (H265)",
                            "Быстрое сжатие (H264)",
                            "Максимальное сжатие (AV1)",
                            "Стандартный (H264)"
                        ],
                        default_value="Оригинальный (AV1 NVENC)",
                        callback=self.on_preset_selected,
                        width=350
                    )

                    with dpg.group(horizontal=True):
                        dpg.add_text("Описание:")
                        dpg.add_text("Оригинальные настройки из исходного проекта", tag="preset_description")

            # Кнопки управления
            with dpg.group(horizontal=True):
                dpg.add_button(label="Начать сжатие", callback=self.on_start, width=150, height=40)
                dpg.add_button(label="Остановить", callback=self.on_stop, width=150, height=40)

            # Прогресс
            dpg.add_text("Общий прогресс:")
            dpg.add_progress_bar(tag="main_progress_bar", width=-1, height=20)

            # Информация о текущем процессе
            with dpg.group(horizontal=True):
                dpg.add_text("Время: 00:00:00.00", tag="current_time")
                dpg.add_spacer(width=20)
                dpg.add_text("Скорость: 0.0x", tag="current_speed")

            # Список файлов
            dpg.add_text("Файлы:")
            with dpg.child_window(tag="file_list", width=-1, height=150):
                pass  # Контент будет добавлен динамически

            # Журнал
            dpg.add_text("Журнал:")
            with dpg.child_window(tag="log_window", width=-1, height=100):
                dpg.add_text("Готов к работе", tag="log")

        # Создание окна
        dpg.create_viewport(title="Видео Компрессор", width=670, height=700)
        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Центрируем окно
        dpg.set_viewport_pos([
            (dpg.get_viewport_client_width() - 670) // 2,
            (dpg.get_viewport_client_height() - 700) // 2
        ])

    def start(self):
        """Запускает основной цикл UI"""
        dpg.start_dearpygui()
        # После закрытия окна освобождаем ресурсы
        self.destroy()

    def update_file_list(self, files, statuses, file_info=None):
        """Обновляет список файлов в UI"""
        dpg.delete_item("file_list", children_only=True)

        for file in files:
            status = statuses[file]

            if status.value == "pending":
                color = (255, 255, 0)  # Желтый
                status_text = "(В ожидании)"
            elif status.value == "processing":
                color = (255, 165, 0)  # Оранжевый
                status_text = "(В процессе)"
            elif status.value == "done":
                color = (0, 255, 0)  # Зеленый
                status_text = "(Готово)"
            else:  # error
                color = (255, 0, 0)  # Красный
                status_text = "(Ошибка)"

            with dpg.group(parent="file_list"):
                info_text = ""
                if file_info and file in file_info:
                    info = file_info[file]
                    size_text = f" - {info.get('size_readable', '?')}"

                    if status.value == "done" and 'output_size_readable' in info:
                        size_text += f" → {info['output_size_readable']} (-{info['compression_ratio']:.1f}%)"

                    info_text = size_text

                dpg.add_text(f"{file} {status_text}{info_text}", color=color)

    def update_progress_bar(self, progress):
        """Обновляет индикатор прогресса"""
        dpg.set_value("main_progress_bar", progress)

    def update_time(self, time):
        """Обновляет отображение текущего времени"""
        dpg.set_value("current_time", f"Время: {time}")

    def update_speed(self, speed):
        """Обновляет отображение текущей скорости"""
        dpg.set_value("current_speed", f"Скорость: {speed}")

    def update_input_folder_label(self, folder):
        """Обновляет отображение входной папки"""
        display_folder = folder
        if len(folder) > 40:
            display_folder = "..." + folder[-40:]
        dpg.set_value("selected_folder", f"Папка: {display_folder}")

    def update_output_folder_label(self, folder):
        """Обновляет отображение выходной папки"""
        display_folder = folder
        if len(folder) > 40:
            display_folder = "..." + folder[-40:]
        dpg.set_value("selected_output_folder", f"Папка: {display_folder}")

    def update_log(self, message):
        """Добавляет сообщение в журнал"""
        current_log = dpg.get_value("log")
        # Ограничиваем журнал последними 10 строками
        log_lines = current_log.split("\n")
        if len(log_lines) > 10:
            log_lines = log_lines[-9:]
        log_lines.append(message)
        dpg.set_value("log", "\n".join(log_lines))

    def show_error(self, message):
        """Показывает окно с ошибкой"""
        with dpg.window(label="Ошибка", modal=True, width=400, height=150, pos=[100, 200]):
            dpg.add_text(message, wrap=380)
            dpg.add_button(label="OK", width=100, callback=lambda: dpg.delete_item(dpg.last_container()))

    def on_select_input_folder(self):
        """Обработчик выбора входной папки"""
        root = Tk()
        root.withdraw()
        folder = filedialog.askdirectory()
        if folder:
            self.controller.on_folder_selected(folder)
            # Если выбрана опция "та же папка", обновляем и выходную папку
            if dpg.get_value("same_folder_checkbox"):
                self.controller.on_output_folder_selected(folder)

    def on_select_output_folder(self):
        """Обработчик выбора выходной папки"""
        if dpg.get_value("same_folder_checkbox"):
            return  # Игнорируем, если выбрана опция "та же папка"

        root = Tk()
        root.withdraw()
        folder = filedialog.askdirectory()
        if folder:
            self.controller.on_output_folder_selected(folder)

    def on_same_folder_toggle(self, sender, app_data):
        """Обработчик переключения опции 'та же папка'"""
        if app_data:  # Если выбрана опция
            # Получаем текущую входную папку
            input_folder = self.controller.model.input_folder
            if input_folder:
                # Устанавливаем выходную папку такой же, как входная
                self.controller.on_output_folder_selected(input_folder)
        else:
            # Сбрасываем состояние выходной папки
            dpg.set_value("selected_output_folder", "Папка: не выбрана")

    def on_input_extension_changed(self, sender, app_data):
        """Обработчик изменения формата входных файлов"""
        self.controller.on_input_extension_changed(app_data)

    def on_output_extension_changed(self, sender, app_data):
        """Обработчик изменения формата выходных файлов"""
        self.controller.on_output_extension_changed(app_data)

    def on_threads_changed(self, sender, app_data):
        """Обработчик изменения количества потоков"""
        self.controller.on_threads_changed(int(app_data))

    def on_preset_selected(self, sender, app_data):
        """Обработчик выбора пресета кодирования"""
        self.controller.on_preset_changed(app_data)

        # Обновляем описание пресета
        description = ""
        if app_data == "Оригинальный (AV1 NVENC)":
            description = "Оригинальные настройки из исходного проекта"
        elif app_data == "Высокое качество (H265)":
            description = "Высокое качество при умеренном размере файла (HEVC)"
        elif app_data == "Быстрое сжатие (H264)":
            description = "Быстрое сжатие с приоритетом скорости над качеством"
        elif app_data == "Максимальное сжатие (AV1)":
            description = "Максимальное сокращение размера файла"
        elif app_data == "Стандартный (H264)":
            description = "Стандартные настройки H264 для совместимости"

        dpg.set_value("preset_description", description)

    def on_start(self):
        """Обработчик нажатия кнопки 'Начать'"""
        self.controller.on_start_compression()

    def on_stop(self):
        """Обработчик нажатия кнопки 'Остановить'"""
        self.controller.on_stop_compression()

    def destroy(self):
        """Освобождает ресурсы UI"""
        dpg.destroy_context()
