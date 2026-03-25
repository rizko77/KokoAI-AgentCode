import time
from datetime import datetime, timezone, timedelta


def get_now():
    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    hari = {
        0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
        4: "Jumat", 5: "Sabtu", 6: "Minggu"
    }
    bulan = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    nama_hari = hari.get(now.weekday(), "")
    nama_bulan = bulan.get(now.month, "")

    return f"{nama_hari}, {now.day} {nama_bulan} {now.year} {now.strftime('%H:%M:%S')} WIB"


def get_timestamp():
    return time.time()


def get_date_iso():
    return datetime.now().isoformat()


def get_uptime_str(start_time):
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)

    if hours > 0:
        return f"{hours}j {minutes}m {seconds}d"
    elif minutes > 0:
        return f"{minutes}m {seconds}d"
    else:
        return f"{seconds}d"
