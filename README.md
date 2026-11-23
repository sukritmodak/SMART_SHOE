# SMART SHOE — Direct USB / Bluetooth Dashboard

A local Windows dashboard for the original ESP32 SMART SHOE prototype. **Firebase has been removed from the application code and data path.** The ESP32 connects directly to the Windows computer through USB Serial or Bluetooth Classic SPP COM port.

## Run the live dashboard

1. Download or clone this repository to your Windows computer.
2. Install Python 3 if needed.
3. Open Command Prompt in the repository folder and install the only dependency:

   ```bat
   py -m pip install --upgrade pyserial
   ```

4. Close Arduino Serial Monitor.
5. Start the bridge:

   ```bat
   py bridge\\smartshoe_bridge.py
   ```

6. Choose `1` for USB cable or `2` for Bluetooth Classic.
7. Select the correct COM port. For Bluetooth, pair `SmartShoe` in Windows first and choose its **outgoing** SPP COM port.
8. Open **http://127.0.0.1:8080** in Chrome or Edge.
9. Keep the command window open while monitoring.

The Python program reads the selected COM port and serves the dashboard locally. The page polls the local bridge for live sensor packets. No Firebase login, API key, database rules, cloud upload or internet account is required. Internet is needed only for online map tiles.

## Live map and GPS

The current ESP32 firmware sends four ultrasonic distances only: `front,left,right,lower`. It has no GPS receiver, so it cannot independently report the shoe's geographic position.

The dashboard's **Start live map** button uses browser geolocation (phone/laptop GPS, if available) and draws a live marker and movement trail. This marks the phone/laptop carrying or running the dashboard, not the shoe independently. A laptop without GPS may provide only approximate or no location.

For independent shoe mapping, add a GPS module such as NEO-6M to the shoe and update the firmware to send latitude and longitude. The local bridge already accepts an optional six-field packet:
`front,left,right,lower,latitude,longitude`.
The present four-sensor firmware does not send those GPS fields yet.

## ESP32 firmware

Open `SMART_SHOE_CLASSIC.ino` in Arduino IDE. For the original ESP32-D0WD-V3 select:

- Board: ESP32 Dev Module
- Flash Size: **4MB (32Mb)**
- Flash Mode: DIO
- Flash Frequency: 40MHz
- Partition Scheme: Default 4MB with spiffs
- Upload Speed: 115200

If available, set Erase All Flash Before Sketch Upload to Enabled for one clean upload, then return it to Disabled. This corrects the 4 MB hardware / 16 MB firmware-header mismatch.

The sketch preserves the sensor pin map and outputs four comma-separated readings at 115200 baud over USB Serial and Bluetooth Classic SPP. HC-SR04 ECHO outputs must be reduced to 3.3 V using a voltage divider; share common ground.

## Optional PlatformIO build

```bash
python -m pip install --upgrade platformio
pio run
```

The `platformio.ini` sets the target flash size to 4 MB.

## Dashboard hosting

The GitHub Pages workflow can still publish the static dashboard, but **GitHub Pages cannot directly access a Windows COM port**. For direct COM operation, use the local dashboard at `http://127.0.0.1:8080` while the Python bridge is running.

## Troubleshooting

- COM port unavailable: close Arduino Serial Monitor and other serial programs.
- Bluetooth not connecting: pair `SmartShoe` and select its outgoing Bluetooth SPP COM port.
- No live sensor data: confirm the firmware is uploaded, baud rate is 115200, and the selected COM port is correct.
- Flash mismatch: rebuild/upload with 4 MB Flash Size, not 16 MB.
- Map not locating: allow browser location permission; phone/laptop location requires an available GPS/location provider.

This is an academic prototype, not a certified child-safety or emergency-response system.
