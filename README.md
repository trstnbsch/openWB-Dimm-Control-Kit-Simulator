# openWB Dimm- & Control-Kit Simulator

Dieses Projekt simuliert ein **openWB Dimm- & Control-Kit** auf einem Raspberry Pi oder Ubuntu-Server. Es ermöglicht die Steuerung der Ladeleistung (Dimmung gemäß §14a EnWG) über MQTT-Signale. 

Der Simulator emuliert die Hardware-Schnittstellen so exakt, dass die openWB (Software 2.x) ihn als originales Hardware-Modul erkennt.

Der Schaltzustand der Steuerbox kann (bspw. per Shelly) per MQTT veröffentlicht werden.


## Schema

![Systemübersicht DuCK Simulator](duck_schema.png)





## 🌟 Features

* **Vollständige Emulation:** Antwortet auf Telnet-Anfragen (Port 8898) und Modbus-Abfragen (Port 8899).
* **MQTT-Bridge:** Übersetzt frei definierbare MQTT-Topics in digitale Modbus-Eingänge (DI1-DI8). Payload on, 1, true, yes oder off, 0, false, no.
* **Web-Interface:** Integrierte Weboberfläche (Port 5555) zur Konfiguration von MQTT-Broker und Topic-Mappings im laufenden Betrieb.
* **Persistenz:** Einstellungen werden in einer `DuCK_config.json` gespeichert und bleiben nach Neustarts erhalten.

---

## 🛠 Installation

### 1. Abhängigkeiten installieren

```bash
sudo apt update
sudo apt install python3-flask python3-paho-mqtt python3-pymodbus -y
```

### 2. Service einrichten

```bash
sudo nano /etc/systemd/system/openwb-dimmControllKit.service
```

```bash
[Unit]
Description=openWB Dimm-Kit Simulator Daemon
# Der Dienst startet erst, wenn das Netzwerk bereit ist
After=network-online.target
Wants=network-online.target

[Service]
# -u sorgt dafür, dass die Logs sofort (unbuffered) im System-Log erscheinen
ExecStart=/usr/bin/python3 -u /usr/local/bin/energie/DuCK.py
WorkingDirectory=/usr/local/bin
# Bei einem Absturz nach 5 Sekunden neu starten
Restart=always
RestartSec=5
User=root
StandardOutput=inherit
StandardError=inherit

[Install]
# Der Dienst soll im normalen Mehrbenutzermodus starten
WantedBy=multi-user.target
```
