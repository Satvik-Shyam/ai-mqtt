# ai-mqtt: IoT Analytics & Automation Platform

## Overview
This project is an IoT analytics and automation platform featuring smart devices, agent-based analytics, and a web dashboard. It supports device simulation, automated control, and real-time monitoring using MQTT and Python.

---

## Quick Start: Running on a New Machine

### 1. Clone the Repository
```sh
git clone https://github.com/Satvik-Shyam/ai-mqtt.git
cd ai-mqtt
```

### 2. Open in VS Code
You can open the project folder directly:
```sh
code .
```

### 3. Set Up a Python Virtual Environment
It is recommended to use Python 3.10+.
```sh
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
If a `requirements.txt` exists:
```sh
pip install -r requirements.txt
```
If not, install the basics (edit as needed):
```sh
pip install paho-mqtt flask pytest
```

### 5. Run the Application
If your app uses Flask (adjust if different):
```sh
export FLASK_APP=app.py  # Or the main file name
export FLASK_ENV=development
flask run
```
Or, if you have a custom runner script, use:
```sh
python main.py
```

### 6. View the Web Dashboard
Open your browser and go to:
```
http://localhost:5000
```
(or the port shown in your terminal)

---

## Project Structure
- `ai_agents/` — AI and analytics agents
- `iot_devices/` — Device simulation and logic
- `intermediary/` — MQTT and middleware
- `static/` — Frontend assets (HTML, JS, CSS)
- `config/` — Configuration files
- `tests/` — Test cases

---

## Running Tests
```sh
pytest
```

---

## Troubleshooting
- Ensure your Python version is 3.10 or higher
- If MQTT broker is required, install Mosquitto or use a public broker
- For missing dependencies, install them with `pip`

---

## Contributing
Pull requests are welcome! For major changes, please open an issue first.

---

## License
[MIT](LICENSE)
