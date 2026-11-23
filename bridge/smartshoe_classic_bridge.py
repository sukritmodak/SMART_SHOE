#!/usr/bin/env python3
"""SMART SHOE Classic Bluetooth SPP -> Firebase bridge (Windows).

Pair the ESP32 with Windows first, then run:
    python bridge/smartshoe_classic_bridge.py COM7

ESP32 must send one newline-terminated CSV line per reading:
    front,left,right,lower
Example:
    45.2,30.5,80.0,25.4

Install dependencies:
    py -m pip install pyserial requests
"""
import getpass
import json
import os
import sys
import time
from urllib.parse import urlencode

import requests
import serial

API_KEY = "AIzaSyA6PudM6OhefgQBPtFdeXvP6gVw6EferN8"
DATABASE_URL = "https://smart-shoe-af984-default-rtdb.asia-southeast1.firebasedatabase.app"
DEVICE_ID = "smartshoe_001"
BAUD_RATE = 115200
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
REFRESH_URL = "https://securetoken.googleapis.com/v1/token"


def firebase_sign_in(email, password):
    response = requests.post(
        AUTH_URL,
        params={"key": API_KEY},
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data["idToken"], data["refreshToken"], time.time() + int(data.get("expiresIn", "3600")) - 90


def refresh_id_token(refresh_token):
    response = requests.post(
        REFRESH_URL,
        params={"key": API_KEY},
        data=urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data["id_token"], data.get("refresh_token", refresh_token), time.time() + int(data.get("expires_in", "3600")) - 90


def upload_readings(session, token, values):
    # One atomic PATCH keeps sensor values and bridge status in sync.
    url = f"{DATABASE_URL}/devices/{DEVICE_ID}.json"
    payload = {
        "sensor_data": values,
        "device_status": {
            "wifi": False,  # Wi-Fi is not used by this SPP bridge architecture.
            "bluetooth": True,
            "online": True,
            "transport": "classic_bluetooth_spp",
            "updated_at": int(time.time() * 1000),
        },
    }
    response = session.patch(url, params={"auth": token}, json=payload, timeout=15)
    response.raise_for_status()


def parse_line(line):
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 4:
        return None
    try:
        values = [float(part) for part in parts[:4]]
    except ValueError:
        return None
    if any(value < 0 or value > 1000 for value in values):
        return None
    return dict(zip(("front", "left", "right", "lower"), values))


def main():
    if len(sys.argv) < 2:
        print("Usage: python bridge/smartshoe_classic_bridge.py COM7")
        print("Find the outgoing Bluetooth COM port in Windows Device Manager.")
        return 2

    port = sys.argv[1]
    email = os.environ.get("SMARTSHOE_FIREBASE_EMAIL") or input("Firebase device email: ").strip()
    password = os.environ.get("SMARTSHOE_FIREBASE_PASSWORD") or getpass.getpass("Firebase device password: ")
    if not email or not password:
        print("Email and password are required.")
        return 2

    print("SMART SHOE Classic Bluetooth SPP Bridge")
    print(f"Bluetooth serial port: {port} at {BAUD_RATE} baud")
    print("Signing in to Firebase…")
    try:
        token, refresh_token, expiry = firebase_sign_in(email, password)
        with serial.Serial(port, BAUD_RATE, timeout=1) as bt, requests.Session() as session:
            print("Bluetooth COM port opened. Waiting for ESP32 CSV lines…")
            while True:
                raw = bt.readline().decode("utf-8", errors="replace").strip()
                if not raw:
                    if time.time() >= expiry:
                        token, refresh_token, expiry = refresh_id_token(refresh_token)
                        print("Firebase token refreshed.")
                    continue
                readings = parse_line(raw)
                if readings is None:
                    print(f"Ignored invalid packet: {raw[:100]}")
                    continue
                try:
                    if time.time() >= expiry:
                        token, refresh_token, expiry = refresh_id_token(refresh_token)
                    upload_readings(session, token, readings)
                    print("Uploaded:", json.dumps(readings))
                except requests.RequestException as exc:
                    print("Firebase upload failed:", exc)
                    time.sleep(2)
    except serial.SerialException as exc:
        print(f"Could not open {port}: {exc}")
        print("Check Windows Bluetooth pairing and select the outgoing COM port.")
        return 1
    except requests.RequestException as exc:
        print("Firebase connection/authentication failed:", exc)
        print("Check Email/Password sign-in, API key, internet and Realtime Database Rules.")
        return 1
    except KeyboardInterrupt:
        print("\nBridge stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
