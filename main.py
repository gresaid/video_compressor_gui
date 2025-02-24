import os
import threading
import queue
import dearpygui.dearpygui as dpg
from tkinter import filedialog, Tk
import subprocess
import re

input_folder = ""
files = []
file_status = {}
progress = 0
threads = 1
q = queue.Queue()
file_extension = "mp4"
output_extension = "mp4"
current_time = ""
current_speed = ""
stop_flag = False


def select_folder():
    global input_folder, files, file_status, progress
    root = Tk()
    root.withdraw()
    input_folder = filedialog.askdirectory()
    if input_folder:
        dpg.set_value("selected_folder", f"Selected Folder: {input_folder}")
        parse_files()


def parse_files():
    global files, file_status, progress
    files = [f for f in os.listdir(input_folder) if f.endswith(f".{file_extension}")]
    file_status = {f: "pending" for f in files}
    progress = 0
    update_file_list()


def update_file_list():
    dpg.delete_item("file_list", children_only=True)
    for file in files:
        color = (
            (255, 255, 0)
            if file_status[file] == "pending"
            else (0, 255, 0) if file_status[file] == "done" else (255, 165, 0)
        )
        status_text = " (In Process)" if file_status[file] == "processing" else ""
        with dpg.group(parent="file_list"):
            dpg.add_text(file + status_text, color=color)


def compress_video(file):
    global progress, current_time, current_speed, stop_flag
    if stop_flag:
        return

    file_status[file] = "processing"
    update_file_list()

    input_path = os.path.join(input_folder, file)
    output_path = os.path.join(
        input_folder, f"compressed_{os.path.splitext(file)[0]}.{output_extension}"
    )
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-c:v",
        "av1_nvenc",
        "-preset",
        "p3",
        "-b_ref_mode",
        "middle",
        "-rc",
        "vbr",
        "-cq",
        "35",
        output_path,
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    for line in process.stderr:
        if stop_flag:
            process.terminate()
            return
        time_match = re.search(r"time=(\d+:\d+:\d+.\d+)", line)
        speed_match = re.search(r"speed=(\d+.\d+x)", line)

        if time_match:
            current_time = time_match.group(1)
            dpg.set_value("current_time", f"Time: {current_time}")

        if speed_match:
            current_speed = speed_match.group(1)
            dpg.set_value("current_speed", f"Speed: {current_speed}")

    process.wait()
    file_status[file] = "done"
    progress += 1
    update_file_list()
    update_progress_bar()


def worker():
    while not q.empty() and not stop_flag:
        file = q.get()
        compress_video(file)
        q.task_done()


def start_compression():
    global threads, stop_flag
    stop_flag = False
    for file in files:
        if file_status[file] == "pending":
            q.put(file)

    for _ in range(threads):
        t = threading.Thread(target=worker)
        t.start()


def stop_compression():
    global stop_flag
    stop_flag = True


def update_progress_bar():
    if files:
        dpg.set_value("progress_bar", progress / len(files))
        dpg.set_value("main_progress_bar", progress / len(files))


def set_threads(sender, app_data):
    global threads
    threads = int(app_data)


def set_file_extension(sender, app_data):
    global file_extension
    file_extension = app_data
    if input_folder:
        parse_files()


def set_output_extension(sender, app_data):
    global output_extension
    output_extension = app_data


dpg.create_context()
with dpg.window(label="Video Compressor", width=600, height=550):
    dpg.add_button(label="Select Folder", callback=select_folder)
    dpg.add_text("Selected Folder: None", tag="selected_folder")
    dpg.add_combo(
        label="Input File Type",
        items=["mp4", "mkv"],
        default_value="mp4",
        callback=set_file_extension,
    )
    dpg.add_combo(
        label="Output File Type",
        items=["mp4", "mkv"],
        default_value="mp4",
        callback=set_output_extension,
    )
    dpg.add_slider_int(
        label="Threads", default_value=1, min_value=1, max_value=8, callback=set_threads
    )
    dpg.add_button(label="Start Compression", callback=start_compression)
    dpg.add_button(label="Stop Compression", callback=stop_compression)
    dpg.add_progress_bar(tag="main_progress_bar", width=-1, height=20)
    dpg.add_progress_bar(tag="progress_bar", width=-1)
    dpg.add_child_window(tag="file_list", width=-1, height=200)
    dpg.add_text("Time: 00:00:00.00", tag="current_time")
    dpg.add_text("Speed: 0.0x", tag="current_speed")

dpg.create_viewport(title="Video Compressor", width=600, height=550)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
