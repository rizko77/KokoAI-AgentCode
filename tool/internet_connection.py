"""
KokoAI - Internet Connection Check
"""
import socket
import requests


def is_connected(timeout=3):
    """Check if internet connection is available."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except OSError:
        return False


def get_connection_info():
    """Get detailed connection status."""
    connected = is_connected()
    if not connected:
        return {"connected": False, "latency_ms": None, "ip": None}

    try:
        import time
        start = time.time()
        resp = requests.get("https://api.ipify.org?format=json", timeout=5)
        latency = round((time.time() - start) * 1000, 1)
        ip = resp.json().get("ip", "unknown")
        return {"connected": True, "latency_ms": latency, "ip": ip}
    except Exception:
        return {"connected": True, "latency_ms": None, "ip": None}
