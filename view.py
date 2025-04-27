#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
View module for Video Compressor application.
Responsible for user interface and user interaction.
"""

import dearpygui.dearpygui as dpg
from tkinter import filedialog, Tk
import os
from typing import Dict, List, Any, Callable


class CompressionView:
    def __init__(self, controller):
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        """Настраивает пользовательский интерфейс"""
        dpg.create_context()

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 6, 4, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6, category=dpg.mvThemeCat_Core)

        dpg.bind_theme(global_theme)

        # Main window
        with dpg.window(label="Video Compressor", width=650, height=650, tag="main_window", no_resize=True):
            # Folder selection
            with dpg.collapsing_header(label="Folders", default_open=True):
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Select input folder", callback=self.on_select_input_folder)
                        dpg.add_text("Folder: not selected", tag="selected_folder")

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Select output folder", callback=self.on_select_output_folder)
                        dpg.add_text("Folder: not selected", tag="selected_output_folder")
                        dpg.add_checkbox(label="Same as input", default_value=True, callback=self.on_same_folder_toggle,
                                         tag="same_folder_checkbox")

            # File settings
            with dpg.collapsing_header(label="File Settings", default_open=True):
                with dpg.group():
                    dpg.add_combo(
                        label="Input file format",
                        items=["mp4", "mkv", "avi", "mov", "webm"],
                        default_value="mp4",
                        callback=self.on_input_extension_changed,
                        width=200
                    )

                    dpg.add_combo(
                        label="Output file format",
                        items=["mp4", "mkv", "avi", "mov", "webm"],
                        default_value="mp4",
                        callback=self.on_output_extension_changed,
                        width=200
                    )

            # Encoding settings
            with dpg.collapsing_header(label="Encoding Settings", default_open=True):
                with dpg.group():
                    dpg.add_slider_int(
                        label="Number of threads",
                        default_value=1,
                        min_value=1,
                        max_value=8,
                        callback=self.on_threads_changed,
                        width=250
                    )

                    dpg.add_combo(
                        label="Encoding preset",
                        items=[
                            "Original (AV1 NVENC)",
                            "GPU (H265)",
                            "GPU (H264)",
                        ],
                        default_value="Original (AV1 NVENC)",
                        callback=self.on_preset_selected,
                        width=350
                    )

                    with dpg.group(horizontal=True):
                        dpg.add_text("Description:")
                        dpg.add_text("Original settings from the initial project", tag="preset_description")

            # Control buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Start Compression", callback=self.on_start, width=150, height=40)
                dpg.add_button(label="Stop", callback=self.on_stop, width=150, height=40)

            # Progress
            dpg.add_text("Overall progress:")
            dpg.add_progress_bar(tag="main_progress_bar", width=-1, height=20)

            # Current process info
            with dpg.group(horizontal=True):
                dpg.add_text("Time: 00:00:00.00", tag="current_time")
                dpg.add_spacer(width=20)
                dpg.add_text("Speed: 0.0x", tag="current_speed")

            # File list
            dpg.add_text("Files:")
            with dpg.child_window(tag="file_list", width=-1, height=150):
                pass  # Content will be added dynamically

            # Log
            dpg.add_text("Log:")
            with dpg.child_window(tag="log_window", width=-1, height=100):
                dpg.add_text("Ready to work", tag="log")

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
        """Updates the file list in the UI"""
        dpg.delete_item("file_list", children_only=True)

        for file in files:
            status = statuses[file]

            if status.value == "pending":
                color = (255, 255, 0)  # Yellow
                status_text = "(Pending)"
            elif status.value == "processing":
                color = (255, 165, 0)  # Orange
                status_text = "(Processing)"
            elif status.value == "done":
                color = (0, 255, 0)  # Green
                status_text = "(Done)"
            else:  # error
                color = (255, 0, 0)  # Red
                status_text = "(Error)"

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
        """Updates the progress bar"""
        dpg.set_value("main_progress_bar", progress)

    def update_time(self, time):
        """Updates the current time display"""
        dpg.set_value("current_time", f"Time: {time}")

    def update_speed(self, speed):
        """Updates the current speed display"""
        dpg.set_value("current_speed", f"Speed: {speed}")

    def update_input_folder_label(self, folder):
        """Updates the input folder display"""
        display_folder = folder
        if len(folder) > 40:
            display_folder = "..." + folder[-40:]
        dpg.set_value("selected_folder", f"Folder: {display_folder}")

    def update_output_folder_label(self, folder):
        """Updates the output folder display"""
        display_folder = folder
        if len(folder) > 40:
            display_folder = "..." + folder[-40:]
        dpg.set_value("selected_output_folder", f"Folder: {display_folder}")

    def update_log(self, message):
        """Adds a message to the log"""
        current_log = dpg.get_value("log")
        # Limit log to the last 10 lines
        log_lines = current_log.split("\n")
        if len(log_lines) > 10:
            log_lines = log_lines[-9:]
        log_lines.append(message)
        dpg.set_value("log", "\n".join(log_lines))

    def show_error(self, message):
        """Shows an error window"""
        with dpg.window(label="Error", modal=True, width=400, height=150, pos=[100, 200]):
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
        """Preset selection handler"""
        self.controller.on_preset_changed(app_data)

        # Update preset description
        description = ""
        if app_data == "Original (AV1 NVENC)":
            description = "Original settings from the initial project"
        elif app_data == "GPU (H265)":
            description = "High quality with moderate file size (HEVC)"
        elif app_data == "GPU (H264)":
            description = "Fast compression prioritizing speed over quality"

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
