# Nitro's Network Monitor — Network Watchtower

A sleek Python-based network monitor designed to keep an eye on multiple devices. Automatically pings devices on your network and logs online/offline status, sends email alerts when a device goes down, and features a cyberpunk-inspired GUI with system tray support.

## 💡 Features

- Monitors multiple IP addresses
- Real-time status updates
- Logs events with timestamps
- Email alerts via Gmail when devices go offline/online
- Custom alert threholds
- Auto-silence for flapping devices
- Splash screen & tray icon support (broken)
- Outage history (last 10 status changes per device)
- "Last seen online" tracking
- Refresh button for instant updates
- Hidden easter egg (try `Ctrl+Shift+H`)
- Cross-tab layout: Monitor • Outage History • About

## 📷 Screenshots

![image](https://github.com/user-attachments/assets/cb84a61a-712e-4dbd-857a-8be00f46e957)

![image](https://github.com/user-attachments/assets/9f5c609f-8663-49ff-813d-5ea65879a35f)

![image](https://github.com/user-attachments/assets/518e6e38-bc15-49e3-a1d8-19e8bc2b4fb5)


## 🚀 Getting Started

1. Clone the repo:
   ```bash
   git clone https://github.com/sirnitro/network-monitor.git
   cd network-monitor
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
3. Run the app:
```bash
python main.py
```
## 🛠 Built With
- Python 3.x
- Tkinter
- ping3
- pystray
- Pillow

## 🧠 Credits
- Developed by Sir Nitro
- Sound design by Windows 😄

## 🧨 Easter Egg
- Press Ctrl+Shift+H... 👀

## 📬 Contact
- Email: nitro7@nitro7.com
- GitHub: github.com/sirnitro

### ✅ `config.json` 

```json
{
  "ping_interval_seconds": 60,
  "gmail": {
    "from": "example.sender@gmail.com",
    "to": "admin.receiver@example.com",
    "app_password": "abc123def456ghi789"
  },
  "devices": [
    {
      "name": "Test Device 1",
      "ip": "192.168.0.101",
      "mac": "AA:BB:CC:DD:EE:01"
    },
    {
      "name": "Test Device 2",
      "ip": "192.168.0.102",
      "mac": "AA:BB:CC:DD:EE:02"
    },
    {
      "name": "Test Device 3",
      "ip": "192.168.0.103",
      "mac": "AA:BB:CC:DD:EE:03"
    }
  ]
}
```
💡 Note: You must use a Gmail App Password instead of your regular Gmail password.
