import threading
import logging
import socket
import time
import json
import os
from flask import Flask, render_template_string, request, redirect
from paho.mqtt import client as mqtt_client
from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# ================== CONFIG MANAGEMENT ==================
CONFIG_FILE = "DuCK_config.json"
DEFAULT_CONFIG = {
    "MQTT_BROKER": "",
    "MQTT_PORT": 1883,
    "MQTT_USER": "",
    "MQTT_PASSWORD": "",
    "TOPIC_MAP": {
        "topic/DI1": 0,
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()

# ================== LOGGING & MODBUS SETUP ==================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("openwb-sim")

MODBUS_PORT = 8899
TELNET_PORT = 8898

store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0] * 1000),
    co=ModbusSequentialDataBlock(0, [0] * 1000),
    hr=ModbusSequentialDataBlock(0, [0] * 1000),
    ir=ModbusSequentialDataBlock(0, [0] * 1000)
)
store.setValues(3, 100, [2])
modbus_context = ModbusServerContext(slaves=store, single=True)

# ================== MQTT CLIENT LOGIK ==================
mqtt_inst = None

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode().strip().lower()
        value = 1 if payload in ("on", "1", "true", "yes") else 0
        
        current_config = load_config()
        if topic in current_config["TOPIC_MAP"]:
            di_index = current_config["TOPIC_MAP"][topic]
            store.setValues(1, di_index, [value])
            log.info(f"MQTT: {topic} -> DI{di_index+1} ist {value}")
    except Exception as e:
        log.error(f"MQTT Fehler: {e}")

def mqtt_thread_func():
    global mqtt_inst
    while True:
        try:
            current_config = load_config()
            log.info(f"MQTT: Verbinde zu {current_config['MQTT_BROKER']}...")
            
            client_id = f"openwb-sim-{int(time.time())}"
            try:
                mqtt_inst = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id)
            except:
                mqtt_inst = mqtt_client.Client(client_id)

            mqtt_inst.username_pw_set(current_config["MQTT_USER"], current_config["MQTT_PASSWORD"])
            mqtt_inst.on_message = on_message
            mqtt_inst.connect(current_config["MQTT_BROKER"], current_config["MQTT_PORT"], 60)
            
            for topic in current_config["TOPIC_MAP"].keys():
                mqtt_inst.subscribe(topic)
                log.info(f"MQTT: Abonniere {topic}")
            
            mqtt_inst.loop_forever()
        except Exception as e:
            log.error(f"MQTT Fehler: {e}. Neustart in 10s...")
            time.sleep(10)

# ================== TELNET SIMULATOR ==================
def telnet_simulator():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("0.0.0.0", TELNET_PORT))
        server_socket.listen(5)
        while True:
            client_sock, _ = server_socket.accept()
            client_sock.sendall(b"\r\nopenWB DimmModul")
            time.sleep(0.5)
            client_sock.close()
    except Exception as e:
        log.error(f"Telnet Fehler: {e}")

# ================== WEB SERVER (FLASK) ==================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>openWB Dimm- und Control-Kit Simulator Config</title>
<style>
    body { font-family: sans-serif; margin: 40px; background: #f4f4f4; }
    .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    input { width: 100%; padding: 8px; margin: 10px 0; box-sizing: border-box; }
    button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
    label { font-weight: bold; }
</style>
</head>
<body>
    <div class="card">
        <h1>openWB Dimm- und Control-Kit Simulator Einstellungen</h1>
        <form method="POST">
            <h3>MQTT Broker</h3>
            <label>IP Adresse:</label><input type="text" name="broker" value="{{config.MQTT_BROKER}}">
            <label>User:</label><input type="text" name="user" value="{{config.MQTT_USER}}">
            <label>Passwort:</label><input type="password" name="pass" value="{{config.MQTT_PASSWORD}}">
            
            <h3>Topic Mapping (DI1 - DI8)</h3>
            {% for i in range(8) %}
            <label>DI{{i+1}} Topic:</label>
            <input type="text" name="topic_{{i}}" value="{{topics[i]}}">
            {% endfor %}
            
            <button type="submit">Speichern & Neustart</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global mqtt_inst
    current_config = load_config()
    
    # Topic Map umdrehen für einfache Anzeige im Formular
    topics = [""] * 8
    for t, idx in current_config["TOPIC_MAP"].items():
        if idx < 8: topics[idx] = t

    if request.method == "POST":
        current_config["MQTT_BROKER"] = request.form.get("broker")
        current_config["MQTT_USER"] = request.form.get("user")
        current_config["MQTT_PASSWORD"] = request.form.get("pass")
        
        new_topics = {}
        for i in range(8):
            t = request.form.get(f"topic_{i}")
            if t: new_topics[t] = i
        current_config["TOPIC_MAP"] = new_topics
        
        save_config(current_config)
        
        # MQTT Client stoppen, damit der Thread ihn neu startet
        if mqtt_inst:
            mqtt_inst.disconnect()
            
        return redirect("/")

    return render_template_string(HTML_TEMPLATE, config=current_config, topics=topics)

def run_webserver():
    app.run(host="0.0.0.0", port=5555)

# ================== START ==================
if __name__ == "__main__":
    threading.Thread(target=mqtt_thread_func, daemon=True).start()
    threading.Thread(target=telnet_simulator, daemon=True).start()
    threading.Thread(target=run_webserver, daemon=True).start()

    log.info(f"Dienste gestartet. Web-Konfig auf http://[IP]:5555")
    
    try:
        StartTcpServer(context=modbus_context, address=("0.0.0.0", MODBUS_PORT), ignore_missing_slaves=True)
    except Exception as e:
        log.error(f"Modbus Fehler: {e}")
