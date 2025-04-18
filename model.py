import os
import re
import queue
import threading
import subprocess
from enum import Enum
from typing import Dict, List, Any, Callable


class FileStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class CompressionModel:
    def __init__(self):
        self.input_folder = ""
        self.output_folder = ""
        self.files = []
        self.file_status = {}
        self.file_info = {}  # Хранит информацию о размере файла и т.д.
        self.progress = 0
        self.threads = 1
        self.file_queue = queue.Queue()
        self.input_extension = "mp4"
        self.output_extension = "mp4"
        self.current_time = "00:00:00.00"
        self.current_speed = "0.0x"
        self.stop_flag = False
        # Предустановленные настройки кодирования
        self.presets = {
            "Оригинальный (AV1 NVENC)": {
                "codec": "av1_nvenc",
                "preset": "p3",
                "b_ref_mode": "middle",
                "rc": "vbr",
                "cq": "35"
            },
            "Высокое качество (H265)": {
                "codec": "hevc_nvenc",
                "preset": "p2",
                "b_ref_mode": "middle",
                "rc": "vbr",
                "cq": "23"
            },
            "Быстрое сжатие (H264)": {
                "codec": "h264_nvenc",
                "preset": "p7",
                "b_ref_mode": "disabled",
                "rc": "vbr",
                "cq": "30"
            },
            "Максимальное сжатие (AV1)": {
                "codec": "av1_nvenc",
                "preset": "p4",
                "b_ref_mode": "middle",
                "rc": "vbr",
                "cq": "45"
            },
            "Стандартный (H264)": {
                "codec": "h264_nvenc",
                "preset": "p4",
                "b_ref_mode": "middle",
                "rc": "vbr",
                "cq": "28"
            }
        }

        # Текущий выбранный пресет
        self.current_preset = "Оригинальный (AV1 NVENC)"
        self.encoder_settings = self.presets[self.current_preset]
        self.worker_threads = []
        self.observers = []

    def add_observer(self, observer):
        """Добавляет наблюдателя в список"""
        self.observers.append(observer)

    def notify_observers(self, event_type, data=None):
        """Уведомляет всех наблюдателей о событии"""
        for observer in self.observers:
            observer.update(event_type, data)

    def set_input_folder(self, folder):
        """Устанавливает входную папку и обновляет список файлов"""
        self.input_folder = folder
        self.notify_observers("folder_changed", folder)
        if not self.output_folder:
            self.output_folder = folder
            self.notify_observers("output_folder_changed", folder)
        self.parse_files()

    def set_output_folder(self, folder):
        """Устанавливает выходную папку"""
        self.output_folder = folder
        self.notify_observers("output_folder_changed", folder)

    def parse_files(self):
        """Ищет файлы с указанным расширением в входной папке"""
        if not self.input_folder:
            return

        try:
            self.files = [f for f in os.listdir(self.input_folder)
                          if f.lower().endswith(f".{self.input_extension.lower()}")]
            self.file_status = {f: FileStatus.PENDING for f in self.files}
            self.file_info = {}

            # Получаем информацию о размере файлов
            for file in self.files:
                path = os.path.join(self.input_folder, file)
                size = os.path.getsize(path)
                self.file_info[file] = {
                    "size": size,
                    "size_readable": self._format_size(size),
                    "output_size": 0,
                    "compression_ratio": 0
                }

            self.progress = 0
            self.notify_observers("files_parsed", self.files)
        except Exception as e:
            self.notify_observers("error", f"Ошибка при обработке файлов: {str(e)}")

    def _format_size(self, size_bytes):
        """Форматирует размер в байтах в читаемый формат"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} ПБ"

    def set_threads(self, threads):
        """Устанавливает количество потоков"""
        self.threads = threads
        self.notify_observers("threads_changed", threads)

    def set_input_extension(self, extension):
        """Устанавливает расширение входных файлов и обновляет список файлов"""
        self.input_extension = extension
        self.notify_observers("input_extension_changed", extension)
        self.parse_files()

    def set_output_extension(self, extension):
        """Устанавливает расширение выходных файлов"""
        self.output_extension = extension
        self.notify_observers("output_extension_changed", extension)

    def set_preset(self, preset_name):
        """Устанавливает пресет кодирования"""
        if preset_name in self.presets:
            self.current_preset = preset_name
            self.encoder_settings = self.presets[preset_name]
            self.notify_observers("preset_changed", preset_name)

    def start_compression(self):
        """Запускает процесс сжатия файлов"""
        if not self.files:
            self.notify_observers("error", "Нет файлов для сжатия")
            return

        if not self.output_folder:
            self.output_folder = self.input_folder

        # Проверяем существование выходной папки
        if not os.path.exists(self.output_folder):
            try:
                os.makedirs(self.output_folder)
            except Exception as e:
                self.notify_observers("error", f"Невозможно создать выходную папку: {str(e)}")
                return

        self.stop_flag = False
        # Сбрасываем очередь
        while not self.file_queue.empty():
            try:
                self.file_queue.get_nowait()
            except queue.Empty:
                break

        # Добавляем файлы в очередь
        for file in self.files:
            if self.file_status[file] == FileStatus.PENDING:
                self.file_queue.put(file)

        # Запускаем потоки
        self.worker_threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._worker)
            t.daemon = True
            t.start()
            self.worker_threads.append(t)

        self.notify_observers("compression_started")

    def stop_compression(self):
        """Останавливает процесс сжатия"""
        self.stop_flag = True
        self.notify_observers("compression_stopped")

    def _worker(self):
        """Рабочий поток для сжатия файлов"""
        while not self.file_queue.empty() and not self.stop_flag:
            try:
                file = self.file_queue.get(timeout=0.5)
                self._compress_video(file)
                self.file_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.notify_observers("error", f"Ошибка в рабочем потоке: {str(e)}")

    def _compress_video(self, file):
        """Сжимает один видеофайл"""
        if self.stop_flag:
            return

        self._update_file_status(file, FileStatus.PROCESSING)

        input_path = os.path.join(self.input_folder, file)
        output_filename = f"compressed_{os.path.splitext(file)[0]}.{self.output_extension}"
        output_path = os.path.join(self.output_folder, output_filename)

        try:
            command = self._build_ffmpeg_command(input_path, output_path)
            process_result = self._run_ffmpeg_process(command, file)

            if process_result and os.path.exists(output_path):
                self._update_file_info(file, output_path)
                self._update_file_status(file, FileStatus.DONE)
                self.progress += 1
                self.notify_observers("progress_updated", self.progress / len(self.files))
            else:
                self._update_file_status(file, FileStatus.ERROR)
                self.notify_observers("error", f"Ошибка сжатия {file}")

        except Exception as e:
            self._update_file_status(file, FileStatus.ERROR)
            self.notify_observers("error", f"Ошибка обработки {file}: {str(e)}")

    def _update_file_status(self, file, status):
        """Обновляет статус файла и уведомляет наблюдателей"""
        self.file_status[file] = status
        self.notify_observers("file_status_changed", {"file": file, "status": status})

    def _build_ffmpeg_command(self, input_path, output_path):
        """Создает команду для ffmpeg на основе текущих настроек"""
        # Применяем текущий пресет
        settings = self.encoder_settings

        # Базовые параметры ffmpeg
        command = [
            "ffmpeg",
            "-y",  # Перезаписывать файлы без запроса
            "-i", input_path,
            "-c:v", settings["codec"],
            "-preset", settings["preset"],
            "-b_ref_mode", settings["b_ref_mode"],
            "-rc", settings["rc"],
            "-cq", settings["cq"]
        ]

        # Добавляем настройки для аудио
        command.extend(["-c:a", "aac", "-b:a", "128k"])

        # Добавляем выходной путь
        command.append(output_path)

        return command

    def _run_ffmpeg_process(self, command):
        """Запускает процесс ffmpeg и обрабатывает его вывод"""
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            for line in process.stderr:
                if self.stop_flag:
                    process.terminate()
                    return False

                self._process_ffmpeg_output_line(line)

            process.wait()
            return process.returncode == 0

        except Exception as e:
            self.notify_observers("error", f"Ошибка запуска ffmpeg: {str(e)}")
            return False

    def _process_ffmpeg_output_line(self, line):
        """Обрабатывает строку вывода ffmpeg"""
        time_match = re.search(r"time=(\d+:\d+:\d+.\d+)", line)
        speed_match = re.search(r"speed=(\d+.\d+x)", line)

        if time_match:
            self.current_time = time_match.group(1)
            self.notify_observers("time_updated", self.current_time)

        if speed_match:
            self.current_speed = speed_match.group(1)
            self.notify_observers("speed_updated", self.current_speed)

    def _update_file_info(self, file, output_path):
        """Обновляет информацию о файле после сжатия"""
        output_size = os.path.getsize(output_path)
        input_size = self.file_info[file]["size"]
        ratio = (input_size - output_size) / input_size * 100 if input_size > 0 else 0

        self.file_info[file].update({
            "output_size": output_size,
            "output_size_readable": self._format_size(output_size),
            "compression_ratio": ratio
        })

        self.notify_observers("file_info_updated", {"file": file, "info": self.file_info[file]})