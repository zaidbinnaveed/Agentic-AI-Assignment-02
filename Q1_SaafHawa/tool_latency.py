"""Measures the latency of SaafHawa's four tools for Karachi and appends every measurement to timing_log.csv.

Tools timed:
  air_quality  - OpenAQ v3 latest PM2.5/PM10 for the nearest Karachi monitoring location (needs OPENAQ_API_KEY in .env)
  weather      - Open-Meteo current temperature, humidity and wind for Karachi (no key)
  heat_index   - NOAA Rothfusz heat-index regression, computed locally
  kb_lookup    - keyword search over the local advisory knowledge base (knowledge_base.json)

Usage: python tool_latency.py [--n 25]   (run on at least two different days; every run appends to the same log)
"""
import argparse
import csv
import json
import os
import re
import socket
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

HERE = Path(__file__).parent
LOG = HERE / "timing_log.csv"
KARACHI = (24.8607, 67.0011)
OPENAQ = "https://api.openaq.org/v3"
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
FIELDS = ["timestamp_utc", "run_id", "host", "tool", "iteration", "latency_ms", "status", "detail"]
KB = json.loads((HERE / "knowledge_base.json").read_text(encoding="utf-8"))


def heat_index_c(temp_c, rh):
    """NOAA/NWS heat index (Rothfusz regression with NWS adjustments), https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml"""
    t = temp_c * 9 / 5 + 32
    hi = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    if (hi + t) / 2 >= 80:
        hi = (-42.379 + 2.04901523 * t + 10.14333127 * rh - 0.22475541 * t * rh - 0.00683783 * t * t
              - 0.05481717 * rh * rh + 0.00122874 * t * t * rh + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh)
        if rh < 13 and 80 <= t <= 112:
            hi -= (13 - rh) / 4 * ((17 - abs(t - 95)) / 17) ** 0.5
        elif rh > 85 and 80 <= t <= 87:
            hi += (rh - 85) / 10 * (87 - t) / 5
    return (hi - 32) * 5 / 9


def kb_lookup(query, k=3):
    words = set(re.findall(r"[a-z0-9.]+", query.lower()))
    scored = sorted(KB, key=lambda e: -len(words & set(e["tags"])))
    return [e["id"] for e in scored[:k]]


def nearest_openaq_location(session):
    params = {"coordinates": f"{KARACHI[0]},{KARACHI[1]}", "radius": 25000, "limit": 50, "parameters_id": 2}
    resp = session.get(f"{OPENAQ}/locations", params=params, timeout=30)
    resp.raise_for_status()
    locations = resp.json()["results"]
    if not locations:
        raise RuntimeError("no OpenAQ PM2.5 location within 25 km of Karachi")
    return min(locations, key=lambda loc: loc.get("distance") or 0)


def openaq_latest(session, location_id):
    resp = session.get(f"{OPENAQ}/locations/{location_id}/latest", timeout=30)
    resp.raise_for_status()
    return len(resp.json()["results"])


def open_meteo_current(session):
    params = {"latitude": KARACHI[0], "longitude": KARACHI[1], "timezone": "Asia/Karachi",
              "current": "temperature_2m,relative_humidity_2m,wind_speed_10m"}
    resp = session.get(OPEN_METEO, params=params, timeout=30)
    resp.raise_for_status()
    cur = resp.json()["current"]
    return cur["temperature_2m"], cur["relative_humidity_2m"], cur["wind_speed_10m"]


def timed(fn):
    start = time.perf_counter()
    try:
        detail = fn()
        status = "ok"
    except Exception as exc:  # log the failure and keep measuring the other tools
        detail, status = f"{type(exc).__name__}: {exc}"[:200], "error"
    return (time.perf_counter() - start) * 1000, status, detail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=25, help="calls per tool (assignment minimum: 20)")
    parser.add_argument("--pause", type=float, default=0.5, help="seconds between API calls")
    args = parser.parse_args()

    load_dotenv(HERE.parent / ".env")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    host = socket.gethostname()
    rows = []

    def log(tool, i, latency, status, detail):
        rows.append({"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "run_id": run_id,
                     "host": host, "tool": tool, "iteration": i, "latency_ms": round(latency, 4), "status": status,
                     "detail": detail})

    weather_session, aq_session = requests.Session(), requests.Session()
    key = os.getenv("OPENAQ_API_KEY")
    location = None
    if key:
        aq_session.headers["X-API-Key"] = key
        try:
            location = nearest_openaq_location(aq_session)
            print(f"OpenAQ location: {location['id']} {location.get('name')} ({location.get('distance')} m)")
        except Exception as exc:
            print(f"OpenAQ location lookup failed: {exc}")
    else:
        print("OPENAQ_API_KEY missing in .env - air_quality calls will be logged as errors")

    temp, rh = 35.0, 60.0
    for i in range(1, args.n + 1):
        latency, status, detail = timed(lambda: open_meteo_current(weather_session))
        if status == "ok":
            temp, rh, _ = detail
        log("weather", i, latency, status, json.dumps(detail) if status == "ok" else detail)

        if location:
            latency, status, detail = timed(lambda: f"{openaq_latest(aq_session, location['id'])} sensors")
        else:
            latency, status, detail = 0.0, "error", "no API key or location"
        log("air_quality", i, latency, status, detail)
        time.sleep(args.pause)

    for i in range(1, args.n + 1):
        latency, status, value = timed(lambda: heat_index_c(temp, rh))
        log("heat_index", i, latency, status, f"T={temp}C RH={rh}% HI={value:.2f}C")
        latency, status, ids = timed(lambda: kb_lookup("is it safe for my asthmatic child to jog outdoors in the heatwave pm2.5"))
        log("kb_lookup", i, latency, status, ",".join(ids))

    new_file = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerows(rows)

    for tool in ("air_quality", "weather", "heat_index", "kb_lookup"):
        ok = [r["latency_ms"] for r in rows if r["tool"] == tool and r["status"] == "ok"]
        median = statistics.median(ok) if ok else float("nan")
        print(f"{tool:12s} ok={len(ok):3d}/{args.n}  median={median:.4f} ms")
    print(f"appended {len(rows)} rows to {LOG.name} (run {run_id})")


if __name__ == "__main__":
    main()
