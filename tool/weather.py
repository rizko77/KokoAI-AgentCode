import requests
from config.settings import REQUEST_TIMEOUT, USER_AGENT


def get_weather(city="Jakarta"):
    try:
        url = f"https://wttr.in/{city}?format=j1"
        headers = {"User-Agent": USER_AGENT}

        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        current = data.get("current_condition", [{}])[0]

        return {
            "city": city,
            "temp_c": current.get("temp_C", "N/A"),
            "feels_like_c": current.get("FeelsLikeC", "N/A"),
            "humidity": current.get("humidity", "N/A"),
            "description": current.get("weatherDesc", [{}])[0].get("value", "N/A"),
            "wind_speed": current.get("windspeedKmph", "N/A"),
            "wind_dir": current.get("winddir16Point", "N/A"),
            "visibility": current.get("visibility", "N/A"),
            "uv_index": current.get("uvIndex", "N/A"),
        }

    except requests.RequestException as e:
        return {"error": f"Gagal mendapatkan cuaca: {e}"}
    except Exception as e:
        return {"error": f"Error: {e}"}


def get_weather_simple(city="Jakarta"):
    try:
        url = f"https://wttr.in/{city}?format=%C+%t+%h"
        headers = {"User-Agent": USER_AGENT}

        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        return response.text.strip()

    except Exception:
        return "Cuaca tidak tersedia"
