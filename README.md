# SMART SHOE — Direct Bluetooth Browser Dashboard

The dashboard reads the ESP32's Bluetooth Classic SPP serial stream directly in the browser using the Web Serial API. **No Python bridge, local relay server, CMD window, Firebase, or cloud database is required.**

## Connect directly

1. Upload `SMART_SHOE_CLASSIC.ino` to an original ESP32 board.
2. In Windows Bluetooth settings, pair with **SmartShoe**.
3. Ensure Windows has created the device's **outgoing Bluetooth SPP COM port**.
4. Open the GitHub Pages dashboard in the latest desktop Google Chrome or Microsoft Edge:
   `https://sukritmodak.github.io/SMART_SHOE/`
5. Click **Connect Bluetooth COM**.
6. In the browser's serial-port chooser, select the outgoing COM port associated with **Standard Serial over Bluetooth link / SmartShoe** and grant permission.
7. The page reads raw newline-terminated CSV packets at **115200 baud**, parses `front,left,right,lower\n`, and processes sensor readings directly in JavaScript.
8. Click **Disconnect** when finished.

## Browser requirements and limitations

- Use desktop Chrome or Edge with Web Serial support. The feature requires a secure context such as GitHub Pages HTTPS or localhost.
- Pair the ESP32 in Windows first. Select the outgoing SPP COM port, not the incoming port.
- Keep the dashboard tab open while monitoring. Browser serial permission is granted by the user through the browser chooser.
- Close Arduino Serial Monitor or any other application using the same COM port.
- Some browser/OS combinations may not expose Bluetooth SPP ports to Web Serial. If the ESP32 COM port does not appear in the chooser, direct browser connection is not supported on that setup; do not use Web Bluetooth because this firmware uses Classic SPP, not BLE GATT.
- Internet is required for OpenStreetMap tiles. Browser geolocation maps the phone/laptop, not the shoe itself.

## Sensor packet and alerts

Current firmware sends four comma-separated ultrasonic distances: `front,left,right,lower\n`. The dashboard processes the raw values locally and shows the four sensor cards, directional obstacle radar, nearest obstacle, and alert severity. Visual/audio alert levels: below 20 cm warning, 10 cm or less danger, 5 cm or less critical. The ESP32 buzzer is configured to activate below 20 cm.

The current firmware has no GPS receiver. For an independent shoe geographic marker, add a GPS module and send `front,left,right,lower,latitude,longitude\n`.

## ESP32 hardware configuration

For original ESP32-D0WD-V3:

- Board: ESP32 Dev Module
- Flash Size: 4MB (32Mb)
- Flash Mode: DIO
- Flash Frequency: 40MHz
- Partition Scheme: Default 4MB with spiffs
- Upload Speed: 115200

HC-SR04 ECHO outputs must be reduced to 3.3 V with voltage dividers; share common ground.

This is an academic prototype, not a certified safety or emergency-response system.
