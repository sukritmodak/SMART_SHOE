#!/usr/bin/env python3
"""SMART SHOE USB-Serial or Classic Bluetooth SPP -> Firebase bridge.

Run from the repository root:
    py -m pip install pyserial requests
    py bridge\\smartshoe_bridge.py

Choose USB cable or Bluetooth, then select the COM port shown by Windows.
The ESP32 sends: front,left,right,lower\n
"""
import getpass
import json
import os
import sys
import time
from urllib.parse import urlencode

import requests
import serial
from serial.tools import list_ports

API_KEY = "AIzaSyA6PudM6OhefgQBPtFdeXvP6gVw6EferN8"
DATABASE_URL = "https://smart-shoe-af984-default-rtdb.asia-southeast1.firebasedatabase.app"
DEVICE_ID = "smartshoe_001"
BAUD_RATE = 115200
AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
REFRESH_URL = "https://securetoken.googleapis.com/v1/token"


def firebase_sign_in(email, password):
    response = requests.post(AUTH_URL, params={"key": API_KEY},
        json={"email": email, "password": password, "returnSecureToken": True}, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data["idToken"], data["refreshToken"], time.time() + int(data.get("expiresIn", "3600")) - 90


def refresh_id_token(refresh_token):
    response = requests.post(REFRESH_URL, params={"key": API_KEY},
        data=urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}),
        headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data["id_token"], data.get("refresh_token", refresh_token), time.time() + int(data.get("expires_in", "3600")) - 90


def upload_readings(session, token, values, transport):
    url = f"{DATABASE_URL}/devices/{DEVICE_ID}.json"
    payload = {
        "sensor_data": values,
        "device_status": {
            "wifi": False,
            "bluetooth": transport == "classic_bluetooth_spp",
            "online": True,
            "transport": transport,
            "updated_at": int(time.time() * 1000),
        },
    }
    response = session.patch(url, params={"auth": token}, json=payload, timeout=15)
    response.raise_for_status()


def parse_line(line):
    parts = [part.strip() for part in line.split(",")]
    if len(parts) != 4:
        return None
    try:
        values = [float(part) for part in parts]
    except ValueError:
        return None
    if any(value < 0 or value > 1000 for value in values):
        return None
    return dict(zip(("front", "left", "right", "lower"), values))


def choose_transport():
    print("\nSelect how the ESP32 is connected:")
    print("  1. USB cable (USB Serial COM port)")
    print("  2. Bluetooth (Classic Bluetooth outgoing COM port)")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice in ("1", "2"):
            return ("usb_serial", "USB Serial") if choice == "1" else ("classic_bluetooth_spp", "Bluetooth SPP")
        print("Please enter 1 or 2.")


def choose_port():
    ports = list(list_ports.comports())
    if ports:
        print("\nDetected Windows serial ports:")
        for index, port in enumerate(ports, 1):
            print(f"  {index}. {port.device} — {port.description}")
    else:
        print("\nNo COM ports detected automatically.")
    while True:
        answer = input("Select port number or type COM name (e.g. COM6): ").strip()
        if answer.upper().startswith("COM"):
            return answer.upper()
        if answer.isdigit() and 1 <= int(answer) <= len(ports):
            return ports[int(answer) - 1].device
        print("Invalid selection. Choose a listed number or type a COM name.")


def main():
    print("=" * 52)
    print("SMART SHOE — USB / BLUETOOTH BRIDGE")
    print("=" * 52)
    transport, transport_label = choose_transport()
    port = choose_port()
    email = os.environ.get("SMARTSHOE_FIREBASE_EMAIL") or input("\nFirebase device email: ").strip()
    password = os.environ.get("SMARTSHOE_FIREBASE_PASSWORD") or getpass.getpass("Firebase device password: ")
    if not email or not password:
        print("Email and password are required.")
        return 2

    print(f"\nTransport: {transport_label}")
    print(f"COM port: {port} at {BAUD_RATE} baud")
    print("Signing in to Firebase…")
    try:
        token, refresh_token, expiry = firebase_sign_in(email, password)
        with serial.Serial(port, BAUD_RATE, timeout=1) as device, requests.Session() as session:
            if transport == "usb_serial":
                # ESP32 boards often reboot when a USB serial port is opened.
                time.sleep(2)
                device.reset_input_buffer()
            print(f"{transport_label} connected. Waiting for sensor CSV data…")
            print("Expected format: front,left,right,lower")
            while True:
                raw = device.readline().decode("utf-8", errors="replace").strip()
                if not raw:
                    if time.time() >= expiry:
                        token, refresh_token, expiry = refresh_id_token(refresh_token)
                        print("Firebase token refreshed.")
                    continue
                readings = parse_line(raw)
                if readings is None:
                    continue
                try:
                    if time.time() >= expiry:
                        token, refresh_token, expiry = refresh_id_token(refresh_token)
                    upload_readings(session, token, readings, transport)
                    print("Uploaded:", json.dumps(readings))
                except requests.RequestException as exc:
                    print("Firebase upload failed:", exc)
                    time.sleep(2)
    except serial.SerialException as exc:
        print(f"Could not open {port}: {exc}")
        print("Check the selected COM port and close Arduino Serial Monitor or other programs using it.")
        return 1
    except requests.RequestException as exc:
        print("Firebase connection/authentication failed:", exc)
        print("Check Email/Password sign-in, internet, API key and Realtime Database Rules.")
        return 1
    except KeyboardInterrupt:
        print("\nBridge stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
