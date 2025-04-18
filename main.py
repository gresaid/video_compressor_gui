#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video Compressor - application for compressing video files using FFmpeg

Structure based on MVC pattern (Model-View-Controller):
- Model: contains data and business logic
- View: responsible for user interface
- Controller: connects model and view
"""

import sys
import os
import traceback
from model import CompressionModel
from view import CompressionView
from controller import CompressionController


def check_requirements():
    """Checks for required dependencies"""
    try:
        import dearpygui.dearpygui
    except ImportError:
        print("Error: DearPyGui library is not installed.")
        print("Install it with: pip install dearpygui")
        return False

    try:
        import tkinter
    except ImportError:
        print("Error: Tkinter library is not installed.")
        print("Install it using your OS package manager.")
        return False

    # Check for ffmpeg
    import subprocess
    try:
        result = subprocess.run(["ffmpeg", "-version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        if result.returncode != 0:
            print("Error: FFmpeg is not found or not installed.")
            print("Install FFmpeg from the official website: https://ffmpeg.org/download.html")
            return False
    except FileNotFoundError:
        print("Error: FFmpeg is not found in PATH.")
        print("Install FFmpeg from the official website: https://ffmpeg.org/download.html")
        return False

    # Check for Arial font
    arial_paths = [
        "C:/Windows/Fonts/arial.ttf",  # Windows
        "/Library/Fonts/Arial.ttf",  # macOS
        "/System/Library/Fonts/Arial.ttf",  # macOS alternative
        "/usr/share/fonts/truetype/msttcorefonts/arial.ttf",  # Linux with msttcorefonts
    ]

    arial_found = False
    for path in arial_paths:
        if os.path.exists(path):
            arial_found = True
            break

    if not arial_found and not os.path.exists("arial.ttf"):
        print("Warning: Arial font not found in standard locations.")
        print("For correct display of text:")

        if sys.platform == "linux":
            print("    sudo apt-get install ttf-mscorefonts-installer")
        elif sys.platform == "darwin":  # macOS
            print("    Install Arial font manually")
        else:
            print("    Copy arial.ttf file to the program folder")

    return True


def main():
    """Точка входа в приложение"""
    if not check_requirements():
        return 1

    try:
        # Создаем экземпляры MVC
        model = CompressionModel()
        controller = CompressionController(model)
        view = CompressionView(controller)
        controller.set_view(view)

        # Запускаем приложение
        view.start()

        return 0

    except ImportError as e:
        # Ошибка импорта модулей
        error_message = f"Ошибка импорта: {str(e)}\n\n"
        error_message += traceback.format_exc()
        _show_error(error_message)
        return 1
    except OSError as e:
        # Ошибка операционной системы (например, доступ к файлам)
        error_message = f"Ошибка системы: {str(e)}\n\n"
        error_message += traceback.format_exc()
        _show_error(error_message)
        return 1
    except ValueError as e:
        # Ошибка в значениях параметров
        error_message = f"Ошибка в параметрах: {str(e)}\n\n"
        error_message += traceback.format_exc()
        _show_error(error_message)
        return 1
    except Exception as e:
        # Обработка других неожиданных ошибок
        error_message = f"Произошла неожиданная ошибка: {str(e)}\n\n"
        error_message += traceback.format_exc()
        _show_error(error_message)
        return 1


def _show_error(error_message):
    """Shows an error message in console and GUI"""
    print(error_message)

    # Try to show message in GUI if possible
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", error_message)
    except Exception:
        # Ignore errors in displaying GUI
        pass


if __name__ == "__main__":
    sys.exit(main())