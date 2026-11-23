#!/usr/bin/env python3
"""SMART SHOE bridge: ESP32 USB Serial OR Windows Classic Bluetooth SPP -> Firebase.

From the repository root:
  py -m pip install --upgrade pyserial requests
  py bridge\\smartshoe_bridge.py

ESP32 line format: front,left,right,lower\n
For Bluetooth, pair "SmartShoe" in Windows and select its OUTGOING SPP COM port.
"""
import getpass
import json
import os
import re
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
    response = requests.post(
        AUTH_URL, params={"key": API_KEY},
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data["idToken"], data["refreshToken"], time.time() + int(data.get("expiresIn", "3600")) - 90


def refresh_id_token(refresh_token):
    response = requests.post(
        REFRESH_URL, params={"key": API_KEY},
        data=urlencode({"grant_type": "refresh_token", "refresh_token": refresh_token}),
        headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=20,
    )
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
    # Accept only four numeric comma-separated values; ignore ESP32 boot/debug text.
    parts = [part.strip() for part in line.strip().split(",")]
    if len(parts) != 4:
        return None
    try:
        values = [float(part) for part in parts]
    except ValueError:
        return None
    if any(not (0 <= value <= 1000) for value in values):
        return None
    return dict(zip(("front", "left", "right", "lower"), values))


def choose_transport():
    print("\nSELECT ESP32 CONNECTION")
    print("  1. USB cable  — USB Serial COM port")
    print("  2. Bluetooth  — Classic SPP OUTGOING COM port")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return "usb_serial", "USB Serial"
        if choice == "2":
            return "classic_bluetooth_spp", "Bluetooth Classic SPP"
        print("Please enter 1 or 2.")


def choose_port(transport):
    ports = list(list_ports.comports())
    print("\nWINDOWS SERIAL PORTS")
    if not ports:
        print("No COM ports detected. Pair SmartShoe or reconnect the USB data cable.")
    else:
        for i, p in enumerate(ports, 1):
            print(f"  {i}. {p.device:8} | {p.description} | {p.hwid}")
    if transport == "classic_bluetooth_spp":
        print("\nIMPORTANT: choose the Bluetooth OUTGOING port for SmartShoe.")
        print("Do NOT choose an incoming Bluetooth port.")
    else:
        print("\nChoose the USB COM port shown under Device Manager > Ports (COM & LPT).")
    while True:
        answer = input("Port number or COM name (e.g. COM7): ").strip().upper()
        if re.fullmatch(r"COM[0-9]+", answer):
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(ports):
            return ports[int(answer) - 1].device
        print("Invalid selection. Enter a listed number or COM name such as COM7.")


def main():
    print("=" * 60)
    print("SMART SHOE — USB / BLUETOOTH → FIREBASE BRIDGE")
    print("=" * 60)
    transport, label = choose_transport()
    port = choose_port(transport)

    email = os.environ.get("SMARTSHOE_FIREBASE_EMAIL") or input("\nFirebase device email: ").strip()
    password = os.environ.get("SMARTSHOE_FIREBASE_PASSWORD") or getpass.getpass("Firebase device password: ")
    if not email or not password:
        print("Firebase email and password are required.")
        return 2

    print(f"\nSelected: {label} on {port}")
    print("Signing in to Firebase...")
    try:
        token, refresh_token, expiry = firebase_sign_in(email, password)
        # Disable hardware flow control: it is not used by ESP32 SPP or USB CSV streaming.
        with serial.Serial(
            port=port, baudrate=BAUD_RATE, timeout=1, write_timeout=2,
            xonxoff=False, rtscts=False, dsrdtr=False,
        ) as device, requests.Session() as session:
            if transport == "usb_serial":
                print("USB serial opened; waiting 2 seconds for ESP32 auto-reset...")
                time.sleep(2)
                device.reset_input_buffer()
            else:
                print("Bluetooth COM port opened. Windows should now establish the SPP link.")
                time.sleep(2)
                device.reset_input_buffer()

            print("\nBRIDGE READY — waiting for ESP32 CSV packets")
            print("Expected: front,left,right,lower")
            print("Keep this window open. Press Ctrl+C to stop.")
            valid_count = 0
            ignored_count = 0
            last_wait_notice = time.time()

            while True:
                try:
                    raw_bytes = device.readline()
                except serial.SerialException:
                    raise
                if not raw_bytes:
                    if time.time() - last_wait_notice >= 8:
                        print("Still waiting for data. Check ESP32 power, pairing, OUTGOING COM port and firmware.")
                        last_wait_notice = time.time()
                    if time.time() >= expiry:
                        token, refresh_token, expiry = refresh_id_token(refresh_token)
                        print("Firebase token refreshed.")
                    continue

                raw = raw_bytes.decode("utf-8", errors="replace").strip().replace("\x00", "")
                readings = parse_line(raw)
                if readings is None:
                    ignored_count += 1
                    if ignored_count <= 5:
                        print("Ignored non-sensor line:", repr(raw[:100]))
                    continue

                if time.time() >= expiry:
                    token, refresh_token, expiry = refresh_id_token(refresh_token)
                try:
                    upload_readings(session, token, readings, transport)
                    valid_count += 1
                    print(f"#{valid_count} uploaded to Firebase:", json.dumps(readings))
                except requests.RequestException as exc:
                    print("FIREBASE UPLOAD ERROR:", exc)
                    time.sleep(2)

    except serial.SerialException as exc:
        print(f"\nCOM PORT ERROR on {port}: {exc}")
        print("1) Close Arduino Serial Monitor and every other serial program.")
        print("2) For Bluetooth, pair SmartShoe and use its OUTGOING COM port.")
        print("3) Remove the old Windows pairing, restart ESP32, then pair again.")
        print("4) Confirm Windows Device Manager shows the selected COM port.")
        return 1
    except requests.HTTPError as exc:
        detail = exc.response.text[:500] if exc.response is not None else str(exc)
        print("\nFIREBASE AUTH/HTTP ERROR:", detail)
        print("Check Email/Password Authentication, the account, API key and database rules.")
        return 1
    except requests.RequestException as exc:
        print("\nNETWORK/FIREBASE ERROR:", exc)
        print("Check internet access and Firebase configuration.")
        return 1
    except KeyboardInterrupt:
        print("\nBridge stopped by user.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
