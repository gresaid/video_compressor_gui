#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controller module for Video Compressor application.
Coordinates interaction between model and view.
"""

from datetime import datetime
from typing import Optional


class CompressionController:
    def __init__(self, model):
        self.model = model
        self.view = None
        self.model.add_observer(self)

    def set_view(self, view):
        """Устанавливает представление для контроллера"""
        self.view = view

    def update(self, event_type, data=None):
        """Метод обратного вызова для обновлений из модели"""
        if not self.view:
            return

        if event_type == "folder_changed":
            self.view.update_input_folder_label(data)
            self._log(f"Выбрана входная папка: {data}")

        elif event_type == "output_folder_changed":
            self.view.update_output_folder_label(data)
            self._log(f"Выбрана выходная папка: {data}")

        elif event_type == "files_parsed":
            self.view.update_file_list(self.model.files, self.model.file_status, self.model.file_info)
            self._log(f"Найдено {len(self.model.files)} файлов")

        elif event_type == "file_status_changed":
            file = data["file"]
            status = data["status"]
            self.view.update_file_list(self.model.files, self.model.file_status, self.model.file_info)

            if status.value == "processing":
                self._log(f"Начато сжатие {file}")
            elif status.value == "done":
                self._log(f"Завершено сжатие {file}")
            elif status.value == "error":
                self._log(f"Ошибка сжатия {file}")

        elif event_type == "file_info_updated":
            self.view.update_file_list(self.model.files, self.model.file_status, self.model.file_info)

        elif event_type == "progress_updated":
            self.view.update_progress_bar(data)

            done_count = sum(1 for s in self.model.file_status.values() if s.value == "done")
            total_count = len(self.model.files)

            if done_count == total_count and total_count > 0:
                self._log(f"Все файлы обработаны ({done_count}/{total_count})")

        elif event_type == "time_updated":
            self.view.update_time(data)

        elif event_type == "speed_updated":
            self.view.update_speed(data)

        elif event_type == "error":
            self._log(f"Ошибка: {data}")
            self.view.show_error(data)

        elif event_type == "compression_started":
            self._log("Начато сжатие...")

        elif event_type == "compression_stopped":
            self._log("Сжатие остановлено пользователем")

    def _log(self, message):
        """Добавляет сообщение в журнал с временной меткой"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.view.update_log(f"[{timestamp}] {message}")

    def on_folder_selected(self, folder):
        """Обработчик выбора входной папки"""
        self.model.set_input_folder(folder)

    def on_output_folder_selected(self, folder):
        """Обработчик выбора выходной папки"""
        self.model.set_output_folder(folder)

    def on_input_extension_changed(self, extension):
        """Обработчик изменения формата входных файлов"""
        self.model.set_input_extension(extension)

    def on_output_extension_changed(self, extension):
        """Обработчик изменения формата выходных файлов"""
        self.model.set_output_extension(extension)

    def on_threads_changed(self, threads):
        """Обработчик изменения количества потоков"""
        self.model.set_threads(threads)

    def on_preset_changed(self, preset_name):
        """Preset change handler"""
        self.model.set_preset(preset_name)
        self._log(f"Selected encoding preset: {preset_name}")

    def on_start_compression(self):
        """Обработчик запуска сжатия"""
        self.model.start_compression()

    def on_stop_compression(self):
        """Обработчик остановки сжатия"""
        self.model.stop_compression()