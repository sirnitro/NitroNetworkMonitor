import json
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext
from ping3 import ping
import logging
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import os
from PIL import Image, ImageTk
import pystray
import sys
import winsound
import webbrowser
import platform

# App metadata
APP_VERSION = "1.3.0"
LAST_UPDATED = "2025-07-07"

# Load config
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

config = load_config()
devices = sorted(config['devices'], key=lambda d: d['name'])
ping_interval = config['ping_interval_seconds']
alert_threshold = config.get('offline_alert_threshold', 3)
email_config = config['gmail']

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Track status
device_status = {device['ip']: None for device in devices}
last_seen = {device['ip']: "N/A" for device in devices}
outage_history = {device['ip']: [] for device in devices}
consecutive_offline = {device['ip']: 0 for device in devices}
silenced = {device['ip']: False for device in devices}

# Icon paths
ICON_PATHS = {
    'online': 'assets/online.png',
    'offline': 'assets/offline.png',
    'unknown': 'assets/unknown.png'
}

# About info
CONTACT_EMAIL = "nitro7@nitro7.com"
GITHUB_URL = "https://github.com/sirnitro"

# Send Email
def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email_config['from']
    msg['To'] = email_config['to']

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_config['from'], email_config['app_password'])
            server.send_message(msg)
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# GUI Setup
class MonitorApp:
    def __init__(self, master):
        self.master = master
        master.title("Nitro's Network Monitor — Network Watchtower")
        master.configure(bg='#0d0d0d')

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#0d0d0d", borderwidth=0)
        style.configure("TNotebook.Tab", background="#111111", foreground="#00ffff", font=('Share Tech Mono', 10, 'bold'))
        style.map("TNotebook.Tab", background=[("selected", "#1f1f1f")], foreground=[("selected", "#39ff14")])

        style.configure("Treeview", background="#0d0d0d", foreground="#e0e0e0", fieldbackground="#0d0d0d", rowheight=24, font=('Share Tech Mono', 10))
        style.configure("Treeview.Heading", background="#111111", foreground="#00ffff", font=('Share Tech Mono', 10, 'bold'))
        style.map("Treeview", background=[("selected", "#113322")])

        self.tab_control = ttk.Notebook(master)
        self.main_frame = tk.Frame(self.tab_control, bg="#0d0d0d")
        self.history_frame = tk.Frame(self.tab_control, bg="#0d0d0d")
        self.about_frame = tk.Frame(self.tab_control, bg="#0d0d0d")
        self.log_frame = tk.Frame(self.tab_control, bg="#0d0d0d")

        self.tab_control.add(self.main_frame, text=' Monitor ')
        self.tab_control.add(self.history_frame, text=' Outage History ')
        self.tab_control.add(self.about_frame, text=' About ')
        self.tab_control.add(self.log_frame, text=' Log File ')
        self.tab_control.pack(expand=1, fill="both")

        self.about_text = tk.Text(self.about_frame, height=14, bg="#0d0d0d", fg="#00ffff", font=("Share Tech Mono", 10), borderwidth=0, highlightthickness=0)
        self.about_text.insert(tk.END, f"Nitro's Network Monitor — Network Watchtower\n")
        self.about_text.insert(tk.END, f"Version: {APP_VERSION}\n")
        self.about_text.insert(tk.END, f"Last Updated: {LAST_UPDATED}\n\n")
        self.about_text.insert(tk.END, "Email: ")
        self.about_text.insert(tk.END, CONTACT_EMAIL + "\n", ("link_email",))
        self.about_text.insert(tk.END, "GitHub: ")
        self.about_text.insert(tk.END, GITHUB_URL + "\n", ("link_github",))
        self.about_text.insert(tk.END, f"\nSystem: {platform.system()} {platform.release()} | Python {platform.python_version()}\n")
        self.about_text.insert(tk.END, "\nPowered by:\n")
        self.about_text.insert(tk.END, "• Python & Tkinter\n")
        self.about_text.insert(tk.END, "• ping3 by Dan Hunsaker\n")
        self.about_text.insert(tk.END, "• Pillow (PIL)\n")
        self.about_text.insert(tk.END, "• pystray\n")
        self.about_text.insert(tk.END, "\nHint: Press Ctrl+Shift+H for a surprise 😉")
        self.about_text.tag_config("link_email", foreground="#00ffff", underline=1)
        self.about_text.tag_config("link_github", foreground="#00ffff", underline=1)
        self.about_text.tag_bind("link_email", "<Button-1>", lambda e: os.system(f'start mailto:{CONTACT_EMAIL}'))
        self.about_text.tag_bind("link_github", "<Button-1>", lambda e: webbrowser.open(GITHUB_URL))
        self.about_text.config(state='disabled')
        self.about_text.pack(padx=10, pady=20, fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=20, bg="#0d0d0d", fg="#00ffff", font=('Courier New', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))

        self.clear_log_btn = tk.Button(self.log_frame, text="Clear Log", command=self.clear_log, bg="#111111", fg="#00ffff")
        self.clear_log_btn.pack(pady=(0, 10))

        self.load_log_file()    

        self.history_text = scrolledtext.ScrolledText(self.history_frame, height=20, bg="#0d0d0d", fg="#00ffff", font=('Courier New', 9))
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        master.bind('<Control-Shift-H>', self.trigger_easter_egg)

        self.status_label = tk.Label(self.main_frame, text="🟢 0 Online | 🔴 0 Offline", font=("Share Tech Mono", 12), fg="#00ffff", bg="#0d0d0d")
        self.status_label.pack(side=tk.TOP, anchor='w', padx=10, pady=5)

        button_frame = tk.Frame(self.main_frame, bg="#0d0d0d")
        button_frame.pack(fill=tk.X, padx=10)
        tk.Button(button_frame, text="Manual Ping", command=self.manual_ping_all, bg="#111111", fg="#00ffff").pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Reload Config", command=self.reload_config, bg="#111111", fg="#00ffff").pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(self.main_frame, columns=('Name', 'Status', 'Last Seen'), show='headings')
        self.tree.heading('Name', text='Device Name')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Last Seen', text='Last Seen')
        self.tree.tag_configure('online', background="#001a00", foreground="#39ff14")
        self.tree.tag_configure('offline', background="#1a0000", foreground="#ff003c")
        self.tree.tag_configure('unknown', background="#1e1e1e", foreground="#ffcc00")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tooltip = tk.Label(self.main_frame, text="", bg="black", fg="#00ffff", font=("Share Tech Mono", 9), bd=1, relief=tk.SOLID)
        self.tree.bind("<Motion>", self.on_hover)

        self.log_box = scrolledtext.ScrolledText(self.main_frame, height=8, state='disabled', bg="#0d0d0d", fg="#e0e0e0", font=('Courier New', 9))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.update_gui()

    def load_log_file(self):
        try:
            with open('logs/monitor.log', 'r') as f:
                self.log_text.config(state='normal')
                self.log_text.delete('1.0', tk.END)
                self.log_text.insert(tk.END, f.read())
                self.log_text.config(state='disabled')
        except Exception as e:
            self.log_text.insert(tk.END, f"Failed to load log file: {e}\n")

    def clear_log(self):
        open('logs/monitor.log', 'w').close()
        self.load_log_file()


    def update_gui(self):
        online_count = 0
        offline_count = 0
        for row in self.tree.get_children():
            self.tree.delete(row)
        for device in devices:
            ip = device['ip']
            name = device['name']
            status = "Unknown"
            tag = 'unknown'
            if ip in device_status and device_status[ip] is not None:
                is_online = device_status[ip]
                tag = 'online' if is_online else 'offline'
                status = "Online" if is_online else "Offline"
                if is_online:
                    last_seen[ip] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    online_count += 1
                else:
                    offline_count += 1
            self.tree.insert('', 'end', values=(name, status, last_seen[ip]), tags=(tag,))

        self.status_label.config(text=f"🟢 {online_count} Online | 🔴 {offline_count} Offline")
        self.update_history_tab()
        self.master.after(5000, self.update_gui)

    def update_history_tab(self):
        self.history_text.config(state='normal')
        self.history_text.delete('1.0', tk.END)
        for device in devices:
            ip = device['ip']
            history = outage_history[ip][-10:]
            self.history_text.insert(tk.END, f"{device['name']}\n")
            for ts, status in history:
                self.history_text.insert(tk.END, f"  {ts}: {status}\n")
        self.history_text.config(state='disabled')

    def log_to_gui(self, message):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        entry = f"{timestamp} {message}"
        self.log_box.configure(state='normal')
        self.log_box.insert(tk.END, entry + '\n')
        self.log_box.configure(state='disabled')
        self.log_box.see(tk.END)

    def trigger_easter_egg(self, event=None):
        win = tk.Toplevel()
        win.configure(bg='black')
        win.geometry('400x150+600+300')
        win.overrideredirect(True)
        label = tk.Label(win, text="You shouldn't be here. Go back to work!\nPwned by The Methodical One", fg="red", bg="black", font=("Consolas", 14, "bold"))
        label.pack(expand=True)
        win.after(3000, win.destroy)

    def manual_ping_all(self):
        for device in devices:
            ip = device['ip']
            name = device['name']
            result = ping(ip, timeout=2)
            status_text = "ONLINE" if result else "OFFLINE"
            self.log_to_gui(f"Manual check: {name} is {status_text}")

    def reload_config(self):
        global config, devices, ping_interval, email_config, alert_threshold
        config = load_config()
        devices = sorted(config['devices'], key=lambda d: d['name'])
        ping_interval = config['ping_interval_seconds']
        alert_threshold = config.get('offline_alert_threshold', 3)
        email_config = config['gmail']
        self.log_to_gui("Configuration reloaded. Status updated at next interval.")

    def on_hover(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            device_name = self.tree.item(item, 'values')[0]
            device = next((d for d in devices if d['name'] == device_name), None)
            if device:
                tip = f"IP: {device['ip']}\nMAC: {device['mac']}"
                self.tooltip.config(text=tip)
                self.tooltip.place(x=event.x_root - self.master.winfo_rootx() + 20,
                                   y=event.y_root - self.master.winfo_rooty() + 10)
        else:
            self.tooltip.place_forget()

# Monitoring Thread
def monitor_devices(app):
    while True:
        for device in devices:
            ip = device['ip']
            name = device['name']
            result = ping(ip, timeout=2)
            is_online = result is not None

            previous = device_status[ip]
            device_status[ip] = is_online

            if not is_online:
                consecutive_offline[ip] += 1
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_text = "OFFLINE"
                message = f"{name} ({ip}) is now {status_text}"
                if consecutive_offline[ip] == alert_threshold and not silenced[ip]:
                    outage_history[ip].append((ts, status_text))
                    logging.info(message)
                    send_email(f"[Alert] {name} is {status_text}", message)
                    silenced[ip] = True
                if previous is not False:
                    # Log GUI regardless of threshold
                    app.log_to_gui(message)

            else:
                if previous is False:
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    status_text = "ONLINE"
                    outage_history[ip].append((ts, status_text))
                    message = f"{name} ({ip}) is now {status_text}"
                    logging.info(message)
                    app.log_to_gui(message)
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    send_email(f"[Alert] {name} is {status_text}", message)
                consecutive_offline[ip] = 0
                silenced[ip] = False
                last_seen[ip] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        time.sleep(ping_interval)

# Main Execution
root = tk.Tk()
app = MonitorApp(root)
monitor_thread = threading.Thread(target=monitor_devices, args=(app,), daemon=True)
monitor_thread.start()
root.mainloop()
