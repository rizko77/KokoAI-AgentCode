import psutil
import time


def get_cpu_percent():
    return psutil.cpu_percent(interval=1)


def get_cpu_info():
    return {
        "percent": psutil.cpu_percent(interval=1),
        "count_logical": psutil.cpu_count(logical=True),
        "count_physical": psutil.cpu_count(logical=False),
        "freq_current": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        "freq_max": psutil.cpu_freq().max if psutil.cpu_freq() else 0,
        "per_cpu": psutil.cpu_percent(interval=1, percpu=True),
    }


def get_cpu_usage_bar(width=30):
    percent = psutil.cpu_percent(interval=1)
    filled = int(width * percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"CPU [{bar}] {percent:.1f}%"


def monitor_cpu(duration=10, interval=1):
    readings = []
    start = time.time()

    while time.time() - start < duration:
        reading = {
            "timestamp": time.time(),
            "percent": psutil.cpu_percent(interval=0),
        }
        readings.append(reading)
        time.sleep(interval)

    return readings
