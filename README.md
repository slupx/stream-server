# AetherStream Server

A lightweight FastAPI message broker/relay and web viewer UI designed to coordinate real-time screen streams with sub-100ms latency.

---

## File Structure

- `server.py`: FastAPI server that brokers raw JPEG bytes from screen capture clients to web viewers.
- `index.html`: Premium real-time viewer interface.
- `requirements.txt`: Minimal packages to run the server.

---

## Installation & Running

### 1. Set Up Environment
Create and activate a virtual environment, then install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Server
Start the server locally:
```bash
python server.py
```

By default, the server runs on localhost (`127.0.0.1:8000`) for local security.

To host the server on a different interface (e.g. to access it over the local network or internet):
```bash
python server.py --host 0.0.0.0 --port 8080
```

> [!WARNING]
> Binding to `0.0.0.0` exposes the server to external networks. Ensure your firewall or cloud security groups are configured properly to prevent unauthorized access.
