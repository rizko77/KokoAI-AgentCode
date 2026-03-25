import psutil


def get_ram_percent():
    return psutil.virtual_memory().percent


def get_ram_info():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "percent": mem.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
        "swap_percent": swap.percent,
    }


def get_ram_usage_bar(width=30):
    mem = psutil.virtual_memory()
    filled = int(width * mem.percent / 100)
    bar = "█" * filled + "░" * (width - filled)
    used = round(mem.used / (1024**3), 1)
    total = round(mem.total / (1024**3), 1)
    return f"RAM [{bar}] {mem.percent:.1f}% ({used}/{total} GB)"


def is_memory_low(threshold=90):
    return psutil.virtual_memory().percent > threshold
