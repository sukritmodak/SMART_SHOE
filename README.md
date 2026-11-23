# SMART SHOE — Parent Safety Dashboard

A responsive GitHub Pages dashboard for the SMART SHOE classic ESP32 (ESP32-D0WD-V3) prototype.

## Website

After GitHub Pages is enabled, open:

https://sukritmodak.github.io/SMART_SHOE/

In **Repository → Settings → Pages**, select **Deploy from a branch**, branch **main**, folder **/(root)**, then Save. The site is static HTML; no build command is required.

## What this version connects to

- **Firebase Realtime Database over Wi-Fi:** signs in through Firebase Email/Password Authentication in the browser, then reads the latest device record every 2 seconds.
- **Classic Bluetooth SPP:** the original ESP32 sends readings over `BluetoothSerial`; a Windows Python bridge reads its paired outgoing COM port and uploads readings to Firebase. GitHub Pages itself cannot open a Classic Bluetooth SPP COM port.
- **Four ultrasonic readings:** front, left, right and lower.
- **Obstacle radar and nearest-obstacle warning.**
- **Demo mode:** simulated readings are clearly labelled as simulated and are not mixed with real device readings.

## Firebase data structure

The current ESP32 firmware writes to:

```text
devices/
  smartshoe_001/
    sensor_data/
      front: number
      left: number
      right: number
      lower: number
    device_status/
      wifi: boolean
      bluetooth: boolean
      online: boolean
```

The dashboard reads `devices/smartshoe_001.json`. It therefore expects the device ID to remain `smartshoe_001`, matching the firmware.

### Firebase setup checklist

1. In Firebase Console → Authentication → Sign-in method, enable **Email/Password**.
2. In Authentication → Settings → Authorized domains, add `sukritmodak.github.io` (the GitHub Pages hostname) if it is not already listed.
3. Create/confirm the account that the ESP32 firmware uses.
4. Create a **Realtime Database** in the same Firebase project and confirm its database URL matches the firmware.
5. Configure Realtime Database Rules so unauthenticated visitors cannot read or write device data. The dashboard signs in and sends its Firebase ID token when reading.
6. Enter the Firebase email and password into the dashboard at runtime. The website does not store the password in its source code.

For a prototype where the same Firebase account is used by the device and parent dashboard, a minimal authenticated-only rule for this device path can be used:

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

This is a basic prototype rule, not a production access-control design. For deployment, use separate device and parent identities with narrowly scoped rules and validate the authenticated user's UID/device ownership. Never set public read/write access.

The Firebase Web API key used by a browser app is a client identifier, not a database password. Protect the data with Authentication and Database Rules. Never put a service-account key or admin credential in this repository.

## Arduino IDE firmware

Open `SMART_SHOE_CLASSIC.ino` in Arduino IDE. Select **ESP32 Dev Module** (the original ESP32-D0WD-V3), choose the correct USB COM port, and upload. The sketch keeps the existing sensor pin mapping and active-HIGH buzzer. It sends the same four-value CSV line over USB Serial and Classic Bluetooth SPP every 500 ms. Use either connection with the Windows bridge; USB Serial runs at 115200 baud.

Required Arduino library: `BluetoothSerial`, included with the Espressif ESP32 Arduino board package. No BLE libraries or Firebase credentials are required in the ESP32 sketch; the Windows bridge handles Firebase authentication and upload.

## Classic Bluetooth SPP protocol (ESP32-D0WD-V3)

This project uses **Bluetooth Classic SPP**, not Web Bluetooth BLE. The browser cannot directly connect to an SPP serial port from a GitHub Pages HTTPS page. The supported path is:

```text
ESP32 BluetoothSerial -> Windows Bluetooth outgoing COM port
                       -> bridge/smartshoe_classic_bridge.py
                       -> Firebase Realtime Database
                       -> GitHub Pages dashboard
```

The ESP32 must send one newline-terminated CSV packet for each sensor update, in this exact order:

```text
front,left,right,lower
45.2,30.5,80.0,25.4
```

### ESP32 firmware requirement

Use the original ESP32 Bluetooth Classic SPP library (not `BLEDevice.h` / `BLEServer.h`):

```cpp
#include "BluetoothSerial.h"
BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("SmartShoe");  // Windows Bluetooth pairing name
}

// Call this after reading the four ultrasonic sensors:
void sendDistances(float front, float left, float right, float lower) {
  SerialBT.printf("%.1f,%.1f,%.1f,%.1f\n", front, left, right, lower);
}
```

The repository root contains `SMART_SHOE_CLASSIC.ino`, which already applies this SPP method while retaining the original sensor pin mapping. This is for the original ESP32 (ESP32-D0WD-V3); ESP32-S3 does not support Bluetooth Classic SPP.

### Windows bridge setup (USB cable or Bluetooth)

1. Power the ESP32.
2. For **USB**, connect the ESP32 to the PC with a data-capable USB cable. For **Bluetooth**, pair **SmartShoe** in Windows Settings → Bluetooth & devices.
3. Open Command Prompt in the downloaded repository folder and install dependencies:

   ```bat
   py -m pip install pyserial requests
   ```

4. Start the unified bridge:

   ```bat
   py bridge\smartshoe_bridge.py
   ```

5. In the terminal menu, choose:
   - `1` for **USB cable / USB Serial COM port**
   - `2` for **Bluetooth / Classic Bluetooth SPP**
6. Select the matching COM port from the detected list. For Bluetooth, choose the **outgoing** COM port assigned to SmartShoe. For USB, choose the serial port that appears when the ESP32 is plugged in.
7. Enter the Firebase Email/Password account when prompted. Keep this terminal window open while using the dashboard.

The bridge uploads `sensor_data` and `device_status` to `devices/smartshoe_001`. It labels the transport as `usb_serial` or `classic_bluetooth_spp`. Close Arduino Serial Monitor before starting the bridge because only one program can normally use a COM port at a time.

**Important:** GitHub Pages is a hosted website and cannot enumerate or open the COM ports on your Windows computer. COM-port selection therefore happens in the local bridge terminal, not inside the website. The dashboard receives the data from Firebase.

Troubleshooting:
- **COM port not listed:** reconnect the USB cable, use a data cable, check Device Manager → Ports (COM & LPT), or re-pair SmartShoe for Bluetooth.
- **COM port cannot open:** close Arduino Serial Monitor and other serial tools; verify the selected port.
- **No sensor values:** upload the latest `SMART_SHOE_CLASSIC.ino` firmware, confirm the CSV output in Arduino Serial Monitor, and verify the correct port.
- **Firebase authentication/permission error:** check the bridge account, Email/Password provider, internet access, database URL and authenticated write rules.

## Demo map and location limitation

Demo mode draws a clearly labelled simulated marker and short route so the map can be checked without GPS. This is not the user's or shoe's real location. In live mode, the marker is shown only when valid GPS coordinates are uploaded.



The ESP32 firmware sends four ultrasonic distances to the Windows bridge; the bridge uploads sensor data and device status to Firebase. It does **not** send GPS coordinates, step count, accelerometer data or battery level. Therefore this dashboard will not invent a child location or show a fake live route. The map will show a marker only after GPS fields are added to the device/cloud data. A GPS source is required on the shoe or a paired child-side phone, and its coordinates must be uploaded to Firebase.

## Troubleshooting

- **Firebase sign-in failed:** check Email/Password Authentication, account credentials, API key/project, and browser network access.
- **Firebase permission denied:** check that Realtime Database exists and its Rules allow authenticated reads for `devices/smartshoe_001`.
- **No device record:** confirm the ESP32 has successfully authenticated and uploaded to the same database URL and device ID.
- **SmartShoe not listed in Windows Bluetooth:** restart the ESP32, remove any old pairing, pair `SmartShoe` again, and check the outgoing COM port.
- **Bridge connects but values do not change:** open Arduino Serial Monitor at 115200 baud and confirm the four readings change; then check that the bridge uses the outgoing COM port.

## Safety and privacy

This is an academic prototype, not a certified child-safety or emergency-response system. Use location tracking transparently with appropriate knowledge and consent. Protect live telemetry with authentication, least-privilege rules and sensible retention. Do not rely on this dashboard as the sole safety measure.

## Phone GPS sharing and accessible voice alerts

The dashboard can use the **phone's own GPS** while the shoe sends obstacle distances through the Classic Bluetooth SPP bridge:

1. Open the GitHub Pages dashboard on an Android phone in Chrome (HTTPS).
2. Sign in to Firebase with an account allowed to read/write `devices/smartshoe_001`.
3. Keep the Windows Classic Bluetooth SPP bridge running. The website reads shoe sensor values from Firebase; no BLE browser connection is used. No ESP32 GPS module is needed for phone-based location.
4. Tap **Share phone live location** and allow the browser's location permission. The phone browser uses Geolocation API and writes `lat`, `lon`, `accuracy_m`, `source`, and `timestamp` to `devices/smartshoe_001/location` in Realtime Database. A parent dashboard signed into the same project can then read and show this location.
5. Tap **Enable voice alerts** once (a user action is required by browser audio policies). When a valid sensor reading reaches 30 cm or less, the browser speaks the direction and distance. Thresholds are 30, 20, 10, 8, 7, 6, 5, 4, 3, 2 and 1 cm. The browser's speech engine and phone media volume control loudness.

**Important limitations:** keep the phone with the person wearing the shoe; phone GPS locates the phone, not the shoe independently. Location sharing needs HTTPS, location permission, internet access and Firebase authentication/database rules that permit the signed-in user to write the location child path. The shoe-to-dashboard connection uses the Windows Classic Bluetooth SPP bridge; it does not use Web Bluetooth. Voice announcements need the page open and the browser active; this is a prototype feature, not a certified assistive or emergency system. Sensor distances are ultrasonic measurements, not object identification.
