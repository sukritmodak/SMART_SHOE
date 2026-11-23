# SMART SHOE — Parent Safety Dashboard

A GitHub Pages dashboard and Windows bridge for the original ESP32 (ESP32-D0WD-V3) SMART SHOE prototype.

## Important: ESP32 flash-size configuration

The original ESP32 board in this project has **4 MB (32 Mb) flash**. The firmware must be built with a 4 MB flash-size setting. If a binary is built with a 16 MB header, the board reports:

`Detected size(4096k) smaller than the size in the binary image header(16384k)`

This is a firmware build-configuration mismatch, not a sensor or Bluetooth-code error.

### Arduino IDE settings

Open `SMART_SHOE_CLASSIC.ino` and select:

| Arduino IDE menu | Setting |
|---|---|
| Tools → Board | ESP32 Arduino → ESP32 Dev Module |
| Tools → Flash Size | **4MB (32Mb)** |
| Tools → Flash Mode | DIO |
| Tools → Flash Frequency | 40MHz |
| Tools → Partition Scheme | Default 4MB with spiffs |
| Tools → Upload Speed | 115200 |

If your installed ESP32 board package presents a different menu layout, select the equivalent 4 MB flash option. Do not select a 16 MB flash setting.

Then select **Tools → Erase All Flash Before Sketch Upload → Enabled** (if available), upload the sketch again, and set this option back to Disabled for normal future uploads. Erasing flash removes stored settings/data.

### Reproducible PlatformIO build

The repository includes `platformio.ini`, configured for the original ESP32 with a 4 MB flash header. With PlatformIO installed, run from the repository root:

```bash
pio run
```

To upload (choose the correct port):

```bash
pio run -t upload --upload-port COM7
```

Replace `COM7` with the ESP32's actual USB COM port. PlatformIO configuration does not change Arduino IDE menu selections; configure Arduino IDE separately using the table above.

## Website

After GitHub Pages is enabled, open:

https://sukritmodak.github.io/SMART_SHOE/

In **Repository → Settings → Pages**, set **Build and deployment → Source** to **GitHub Actions**. The workflow `.github/workflows/deploy-pages.yml` deploys the root `index.html` on pushes to `main`.

## System architecture

```text
ESP32 sensor firmware
  ├── USB Serial ───────────┐
  └── Bluetooth Classic SPP ┤
                            v
                   Windows Python bridge
                            |
                            v
                    Firebase Realtime DB
                            |
                            v
                    GitHub Pages dashboard
```

GitHub Pages cannot directly enumerate or open Windows COM ports. The local Python bridge handles the USB or Bluetooth COM port and uploads readings to Firebase. Keep the bridge terminal open while using the dashboard.

## Firmware and sensor protocol

The root file `SMART_SHOE_CLASSIC.ino` is for the original ESP32 (ESP32-D0WD-V3), not ESP32-S3. It uses:

- Classic Bluetooth SPP device name: `SmartShoe`
- USB Serial baud rate: 115200
- Four ultrasonic readings in this CSV order: `front,left,right,lower`
- Newline-terminated CSV output every 500 ms
- Active-HIGH buzzer alert when any valid measured distance is at or below 80 cm
- Existing sensor pin mapping retained

Example packet:

```text
45.2,30.5,80.0,25.4
```

HC-SR04 ECHO pins output 5 V and must be reduced to 3.3 V with a voltage divider before connecting to ESP32 GPIO. All modules must share ground.

## Windows bridge setup (USB cable or Bluetooth)

Install dependencies:

```bat
py -m pip install --upgrade pyserial requests
```

Run the unified bridge from the repository root:

```bat
py bridge\\smartshoe_bridge.py
```

Choose:
- `1` for USB Serial
- `2` for Bluetooth Classic SPP

Select the matching COM port. For Bluetooth, first pair **SmartShoe** in Windows Bluetooth settings and choose its **outgoing** SPP COM port, not the incoming port. Enter the Firebase Email/Password account when prompted. Close Arduino Serial Monitor before opening the same COM port in the bridge.

The bridge uploads to Firebase path `devices/smartshoe_001`. It writes `sensor_data` and `device_status`, including the selected transport.

## Firebase configuration

Project ID: `smart-shoe-af984`

Realtime Database URL:

`https://smart-shoe-af984-default-rtdb.asia-southeast1.firebasedatabase.app`

The browser dashboard and bridge use Firebase Email/Password Authentication. Enable that provider in Firebase Authentication and ensure the signed-in account has the required database permissions. Add `sukritmodak.github.io` to Firebase Authentication authorized domains if needed.

A basic authenticated-only prototype rule for this device path is:

```json
{
  "rules": {
    "devices": {
      "smartshoe_001": {
        ".read": "auth != null",
        ".write": "auth != null"
      }
    }
  }
}
```

This is a prototype rule, not a production access-control design. Use separate identities and narrowly scoped rules for a real deployment. Never enable public read/write access or put service-account credentials in this repository.

## Dashboard capabilities and limitations

The dashboard reads the device record from Firebase and displays the four ultrasonic distances, obstacle status and radar visualization. Demo readings are simulated and labelled as demo data.

The ESP32 firmware sends ultrasonic distances only; it does not independently provide GPS, step count, accelerometer data or battery level. The dashboard must not be treated as showing shoe GPS unless a valid location source is actually uploaded. Phone-based location sharing, if used, locates the phone rather than the shoe.

## Troubleshooting

- **Flash-size mismatch / reboot loop:** select 4 MB flash in Arduino IDE, erase flash once, and upload again. Check that the selected board is the original ESP32, not ESP32-S3.
- **Bluetooth device not visible:** restart the ESP32, remove any stale Windows pairing, and pair `SmartShoe` again.
- **No Bluetooth data:** choose the Windows outgoing SPP COM port and check that the bridge reports incoming CSV packets.
- **COM port cannot open:** close Arduino Serial Monitor and other serial applications.
- **No sensor values:** check the wiring, common ground, 3.3 V-safe ECHO dividers, and CSV output at 115200 baud.
- **Firebase authentication/permission error:** verify the Email/Password provider, account credentials, database URL and authenticated database rules.
- **Dashboard not updated:** confirm GitHub Pages uses GitHub Actions and that the latest Actions deployment succeeded.

This is an academic prototype, not a certified child-safety or emergency-response system. Do not rely on it as the sole safety measure.
