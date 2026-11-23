#!/usr/bin/env python3
"""SMART SHOE local COM bridge and dashboard. No Firebase/cloud service."""
import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import serial
from serial.tools import list_ports

ROOT = Path(__file__).resolve().parent.parent
DEVICE_BAUD = 115200
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8080
STATE = {
    "latest": None, "bridge_status": "Starting", "error": None,
    "port": None, "transport_label": None
}
LOCK = threading.Lock()


def choose_transport():
    print("\nSELECT ESP32 CONNECTION")
    print("  1. USB cable — USB Serial COM port")
    print("  2. Bluetooth — Classic Bluetooth SPP OUTGOING COM port")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return "USB Serial"
        if choice == "2":
            return "Bluetooth Classic SPP"
        print("Please enter 1 or 2.")


def choose_port(transport):
    ports = list(list_ports.comports())
    print("\nAVAILABLE WINDOWS COM PORTS")
    for i, p in enumerate(ports, 1):
        print(f"  {i}. {p.device:8} | {p.description}")
    if transport.startswith("Bluetooth"):
        print("\nChoose SmartShoe's OUTGOING Bluetooth COM port, not incoming.")
    else:
        print("\nChoose the USB COM port shown in Device Manager.")
    while True:
        answer = input("COM port number or name (e.g. COM7): ").strip().upper()
        if re.fullmatch(r"COM[0-9]+", answer):
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(ports):
            return ports[int(answer) - 1].device
        print("Invalid COM port selection.")


def parse_packet(line):
    parts = [p.strip() for p in line.strip().split(",")]
    if len(parts) not in (4, 6):
        return None
    try:
        nums = [float(x) for x in parts]
    except ValueError:
        return None
    if any(not (0 <= x <= 1000) for x in nums[:4]):
        return None
    result = dict(zip(("front", "left", "right", "lower"), nums[:4]))
    # Optional future format: front,left,right,lower,latitude,longitude.
    if len(nums) == 6 and -90 <= nums[4] <= 90 and -180 <= nums[5] <= 180:
        result["latitude"], result["longitude"] = nums[4], nums[5]
    return result


def serial_reader(port, transport):
    try:
        with serial.Serial(port, DEVICE_BAUD, timeout=1,
                           xonxoff=False, rtscts=False, dsrdtr=False) as device:
            if transport == "USB Serial":
                time.sleep(2)
                device.reset_input_buffer()
            with LOCK:
                STATE["bridge_status"] = "Connected — receiving serial data"
            print(f"\nConnected to {port} at {DEVICE_BAUD} baud.")
            print("Waiting for ESP32 packets. Keep this window open.")
            while True:
                raw = device.readline().decode("utf-8", errors="replace").strip().replace("\x00", "")
                if not raw:
                    continue
                readings = parse_packet(raw)
                if readings is None:
                    continue
                packet = {
                    **readings,
                    "received_at": time.time(),
                    "transport_label": transport,
                    "port": port
                }
                with LOCK:
                    STATE["latest"] = packet
                    STATE["error"] = None
                print("LIVE:", raw)
    except Exception as exc:
        with LOCK:
            STATE["bridge_status"] = "COM connection error"
            STATE["error"] = str(exc)
        print(f"\nCOM CONNECTION ERROR: {exc}")
        print("Close Arduino Serial Monitor. For Bluetooth, select the outgoing SPP COM port.")
        print("Restart this program after correcting the port.")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/data":
            with LOCK:
                payload = json.dumps(STATE).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if self.path in ("/", "/index.html"):
            file_path = ROOT / "index.html"
            try:
                payload = file_path.read_bytes()
            except OSError:
                self.send_error(404, "index.html missing from repository root")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_error(404)

    def log_message(self, fmt, *args):
        return


def main():
    print("=" * 58)
    print("SMART SHOE — DIRECT USB / BLUETOOTH COM DASHBOARD")
    print("No Firebase. No cloud account. Local computer only.")
    print("=" * 58)
    transport = choose_transport()
    port = choose_port(transport)
    with LOCK:
        STATE["port"] = port
        STATE["transport_label"] = transport
        STATE["bridge_status"] = "Opening COM port"
    threading.Thread(target=serial_reader, args=(port, transport), daemon=True).start()
    server = ThreadingHTTPServer((HTTP_HOST, HTTP_PORT), Handler)
    print(f"\nDASHBOARD: http://{HTTP_HOST}:{HTTP_PORT}")
    print("Open this address in Chrome or Edge.")
    print("Press Ctrl+C here to stop the dashboard and COM connection.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SMART SHOE dashboard...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
