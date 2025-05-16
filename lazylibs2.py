import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import threading
import json
import os

CONFIG_FILE = "config.json"

root = tk.Tk()
root.title("Lazylibraries")
root.geometry("720x600")

# --- Сохранение пути к Python ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f)

config = load_config()

# --- Вспомогательные функции ---
def get_default_python():
    return config.get("python_path") or "python"

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def fetch_installed_packages():
    try:
        result = subprocess.run(
            [get_default_python(), '-m', 'pip', 'list', '--format=json'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return []

# --- Верхняя панель ---
frame_top = tk.Frame(root)
frame_top.pack(fill='x')

label_title = tk.Label(frame_top, text="Lazylibraries", font=("Arial", 20))
label_title.pack(pady=10)

frame_buttons = tk.Frame(root)
frame_buttons.pack(fill='x')

btn_install_mode = tk.Button(frame_buttons, text="Установка")
btn_packages_mode = tk.Button(frame_buttons, text="Библиотеки")
btn_manage_mode = tk.Button(frame_buttons, text="Управление")
btn_help = tk.Button(frame_buttons, text="Справка")

btn_install_mode.pack(side='left', padx=5)
btn_packages_mode.pack(side='left', padx=5)
btn_manage_mode.pack(side='left', padx=5)
btn_help.pack(side='right', padx=5)

# --- Установка ---
frame_install = tk.Frame(root)

label_entry = tk.Label(frame_install, text="Введите название библиотеки:")
label_entry.pack(pady=5)
entry_package = tk.Entry(frame_install, width=40)
entry_package.pack()

label_version = tk.Label(frame_install, text="Введите версию (опционально):")
label_version.pack(pady=5)
entry_version = tk.Entry(frame_install, width=40)
entry_version.pack()

label_python = tk.Label(frame_install, text="Путь к Python (опционально):")
label_python.pack(pady=5)
entry_python = tk.Entry(frame_install, width=40)
entry_python.pack()
entry_python.insert(0, config.get("python_path", ""))

def install_package():
    name = entry_package.get().strip()
    version = entry_version.get().strip()
    path = entry_python.get().strip()
    if path:
        config["python_path"] = path
        save_config(config)
    python_path = path or get_default_python()
    if not name:
        messagebox.showerror("Ошибка", "Введите имя библиотеки")
        return

    full = f"{name}=={version}" if version else name
    label_status.config(text=f"Установка {full}...")
    progress_bar.pack(pady=5)
    progress_bar.start(10)

    def run():
        try:
            result = subprocess.run([python_path, '-m', 'pip', 'install', full],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            msg = f"Установлено: {full}" if result.returncode == 0 else result.stderr
        except Exception as e:
            msg = str(e)

        def update():
            progress_bar.stop()
            progress_bar.pack_forget()
            label_status.config(text=msg)

        root.after(0, update)

    threading.Thread(target=run).start()

btn_install = tk.Button(frame_install, text="Установить", command=install_package)
btn_install.pack(pady=10)

# --- Общий статус и прогресс ---
label_status = tk.Label(root, text="", font=("Arial", 12))
label_status.pack(pady=5)
progress_bar = ttk.Progressbar(root, mode='indeterminate')

# --- Библиотеки ---
frame_packages = tk.Frame(root)
canvas_pkg = tk.Canvas(frame_packages)
scrollbar_pkg = ttk.Scrollbar(frame_packages, orient="vertical", command=canvas_pkg.yview)
scrollable_pkg = tk.Frame(canvas_pkg)
scrollable_pkg.bind("<Configure>", lambda e: canvas_pkg.configure(scrollregion=canvas_pkg.bbox("all")))
canvas_pkg.create_window((0,0), window=scrollable_pkg, anchor="nw")
canvas_pkg.configure(yscrollcommand=scrollbar_pkg.set)
canvas_pkg.pack(side="left", fill="both", expand=True)
scrollbar_pkg.pack(side="right", fill="y")

# --- Управление ---
frame_manage = tk.Frame(root)
canvas_manage = tk.Canvas(frame_manage)
scrollbar_manage = ttk.Scrollbar(frame_manage, orient="vertical", command=canvas_manage.yview)
scrollable_manage = tk.Frame(canvas_manage)
scrollable_manage.bind("<Configure>", lambda e: canvas_manage.configure(scrollregion=canvas_manage.bbox("all")))
canvas_manage.create_window((0,0), window=scrollable_manage, anchor="nw")
canvas_manage.configure(yscrollcommand=scrollbar_manage.set)
canvas_manage.pack(side="left", fill="both", expand=True)
scrollbar_manage.pack(side="right", fill="y")

# --- Режимы ---
def show_install_mode():
    frame_packages.pack_forget()
    frame_manage.pack_forget()
    frame_install.pack(pady=10)
    label_status.config(text="")
    btn_install_mode.config(relief='sunken')
    btn_packages_mode.config(relief='raised')
    btn_manage_mode.config(relief='raised')

def show_packages_mode():
    frame_install.pack_forget()
    frame_manage.pack_forget()
    frame_packages.pack(fill='both', expand=True)
    label_status.config(text="Загрузка списка...")
    btn_install_mode.config(relief='raised')
    btn_packages_mode.config(relief='sunken')
    btn_manage_mode.config(relief='raised')

    clear_frame(scrollable_pkg)
    progress_bar.pack(pady=5)
    progress_bar.start(10)

    def load():
        packages = fetch_installed_packages()
        def draw():
            progress_bar.stop()
            progress_bar.pack_forget()
            label_status.config(text="")
            for pkg in packages:
                f = tk.Frame(scrollable_pkg, pady=5)
                f.pack(fill='x')
                tk.Label(f, text=pkg['name'], font=("Arial", 14, "bold")).pack(anchor='w')
                tk.Label(f, text=f"Версия: {pkg['version']}", font=("Arial", 10)).pack(anchor='w')
                btn_info = tk.Button(f, text="Вывести больше информации", command=lambda name=pkg['name']: show_details(name))
                btn_info.pack(anchor='e')
        root.after(0, draw)

    threading.Thread(target=load).start()

def show_manage_mode():
    frame_install.pack_forget()
    frame_packages.pack_forget()
    frame_manage.pack(fill='both', expand=True)
    label_status.config(text="")
    btn_install_mode.config(relief='raised')
    btn_packages_mode.config(relief='raised')
    btn_manage_mode.config(relief='sunken')

    clear_frame(scrollable_manage)
    progress_bar.pack(pady=5)
    progress_bar.start(10)

    def load():
        packages = fetch_installed_packages()
        def draw():
            progress_bar.stop()
            progress_bar.pack_forget()
            for pkg in packages:
                f = tk.Frame(scrollable_manage, pady=7, bd=1, relief='solid')
                f.pack(fill='x', padx=5)
                tk.Label(f, text=pkg['name'], font=("Arial", 14, "bold")).pack(anchor='w')
                tk.Label(f, text=f"Версия: {pkg['version']}", font=("Arial", 10)).pack(anchor='w')
                btns = tk.Frame(f)
                btns.pack(anchor='w', pady=5)

                def uninstall(name=pkg['name']):
                    answer = messagebox.askyesno("Подтверждение", f"Удалить {name}?")
                    if not answer:
                        return
                    label_status.config(text=f"Удаление {name}...")
                    progress_bar.pack(pady=5)
                    progress_bar.start(10)
                    def run():
                        subprocess.run([get_default_python(), '-m', 'pip', 'uninstall', '-y', name])
                        root.after(0, show_manage_mode)
                    threading.Thread(target=run).start()

                def upgrade(name=pkg['name']):
                    label_status.config(text=f"Обновление {name}...")
                    progress_bar.pack(pady=5)
                    progress_bar.start(10)
                    def run():
                        subprocess.run([get_default_python(), '-m', 'pip', 'install', '--upgrade', name])
                        root.after(0, show_manage_mode)
                    threading.Thread(target=run).start()

                tk.Button(btns, text="Удалить", command=uninstall).pack(side='left', padx=5)
                tk.Button(btns, text="Обновить", command=upgrade).pack(side='left', padx=5)

        root.after(0, draw)

    threading.Thread(target=load).start()

def show_details(name):
    result = subprocess.run([get_default_python(), '-m', 'pip', 'show', name],
                            stdout=subprocess.PIPE, text=True)
    win = tk.Toplevel(root)
    win.title(f"Информация о {name}")
    txt = tk.Text(win, wrap='word')
    txt.insert('1.0', result.stdout)
    txt.pack(expand=True, fill='both')

btn_install_mode.config(command=show_install_mode)
btn_packages_mode.config(command=show_packages_mode)
btn_manage_mode.config(command=show_manage_mode)

show_install_mode()
root.mainloop()
