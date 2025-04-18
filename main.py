import sys
import traceback
from model import CompressionModel
from view import CompressionView
from controller import CompressionController


def check_requirements():
    """Проверяет наличие необходимых зависимостей"""
    try:
        import dearpygui.dearpygui
    except ImportError:
        print("Ошибка: Не установлена библиотека dearpygui.")
        print("Установите ее с помощью: pip install dearpygui")
        return False

    try:
        import tkinter
    except ImportError:
        print("Ошибка: Не установлена библиотека tkinter.")
        print("Установите ее с помощью менеджера пакетов вашей ОС.")
        return False

    # Проверяем наличие ffmpeg
    import subprocess
    try:
        result = subprocess.run(["ffmpeg", "-version"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        if result.returncode != 0:
            print("Ошибка: FFmpeg не найден или не установлен.")
            print("Установите FFmpeg с официального сайта: https://ffmpeg.org/download.html")
            return False
    except FileNotFoundError:
        print("Ошибка: FFmpeg не найден в PATH.")
        print("Установите FFmpeg с официального сайта: https://ffmpeg.org/download.html")
        return False

    return True


def main():
    """Точка входа в приложение"""
    # if not check_requirements():
    #     return 1

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
    """Показывает сообщение об ошибке в консоли и GUI"""
    print(error_message)

    # Пытаемся показать сообщение в GUI, если возможно
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка", error_message)
    except Exception:
        # Игнорируем ошибки отображения GUI
        pass


if __name__ == "__main__":
    sys.exit(main())
