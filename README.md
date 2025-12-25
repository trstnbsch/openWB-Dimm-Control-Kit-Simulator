# openWB Dimm- & Control-Kit Simulator

Dieses Projekt simuliert ein **openWB Dimm- & Control-Kit** auf einem Raspberry Pi oder Ubuntu-Server. Es ermöglicht die Steuerung der Ladeleistung (Dimmung gemäß §14a EnWG) über MQTT-Signale. 

Der Simulator emuliert die Hardware-Schnittstellen so exakt, dass der openWB-Core (Software 2.x) ihn als originales Hardware-Modul erkennt.

## 🌟 Features

* **Vollständige Emulation:** Antwortet auf Telnet-Anfragen (Port 8898) und Modbus-Abfragen (Port 8899).
* **MQTT-Bridge:** Übersetzt frei definierbare MQTT-Topics in digitale Modbus-Eingänge (DI1-DI8).
* **Web-Interface:** Integrierte Weboberfläche (Port 5555) zur Konfiguration von MQTT-Broker und Topic-Mappings im laufenden Betrieb.
* **Persistenz:** Einstellungen werden in einer `DuCK_config.json` gespeichert und bleiben nach Neustarts erhalten.

---

## 🛠 Installation

### 1. Abhängigkeiten installieren

```bash
sudo apt update
sudo apt install python3-flask python3-paho-mqtt python3-pymodbus -y
