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

Keep the existing ultrasonic pin mapping and sensor measurement code. Replace BLE advertising/notifications with the SPP send function above. This Classic Bluetooth method is for the original ESP32 (ESP32-D0WD-V3); ESP32-S3 does not support Bluetooth Classic SPP.

### Windows bridge setup

1. Power the ESP32 and pair **SmartShoe** in Windows Settings → Bluetooth & devices.
2. Open Device Manager → Ports (COM & LPT), or Windows Bluetooth COM port settings, and identify the **outgoing** COM port assigned to SmartShoe.
3. Install dependencies from the repository folder:

   ```bat
   py -m pip install pyserial requests
   ```

4. Run the bridge, replacing COM7 with the outgoing port:

   ```bat
   py bridge\\smartshoe_classic_bridge.py COM7
   ```

5. Enter the Firebase Email/Password account when prompted. Do not put the password in the source code. The account must be permitted by Realtime Database Rules to write `devices/smartshoe_001`.
6. Sign in to the dashboard with an account permitted to read the same device path:

   https://sukritmodak.github.io/SMART_SHOE/

The bridge uploads `sensor_data` and `device_status` to the existing `smartshoe_001` device record. The website continues to poll Firebase; no BLE browser connection is needed. Keep the bridge window running while using Classic Bluetooth.

Troubleshooting:
- **COM port cannot open:** check pairing, choose the outgoing rather than incoming COM port, and close other serial terminal/bridge programs.
- **No CSV packets:** confirm firmware calls `SerialBT.begin("SmartShoe")` and sends newline-terminated comma-separated values.
- **Firebase authentication/permission error:** check the bridge account, Email/Password provider, internet access, database URL and authenticated write rules.

## Demo map and location limitation

Demo mode draws a clearly labelled simulated marker and short route so the map can be checked without GPS. This is not the user's or shoe's real location. In live mode, the marker is shown only when valid GPS coordinates are uploaded.



The current ESP32 firmware uploads only four ultrasonic distances and device status. It does **not** send GPS coordinates, step count, accelerometer data or battery level. Therefore this dashboard will not invent a child location or show a fake live route. The map will show a marker only after GPS fields are added to the device/cloud data. A GPS source is required on the shoe or a paired child-side phone, and its coordinates must be uploaded to Firebase.

## Troubleshooting

- **Firebase sign-in failed:** check Email/Password Authentication, account credentials, API key/project, and browser network access.
- **Firebase permission denied:** check that Realtime Database exists and its Rules allow authenticated reads for `devices/smartshoe_001`.
- **No device record:** confirm the ESP32 has successfully authenticated and uploaded to the same database URL and device ID.
- **BLE device not listed:** ensure the ESP32 is powered, advertising, and using the service UUID above. Use HTTPS and a supported browser.
- **BLE connects but values do not change:** verify the characteristic UUID and that notifications contain four comma-separated numeric values in front,left,right,lower order.

## Safety and privacy

This is an academic prototype, not a certified child-safety or emergency-response system. Use location tracking transparently with appropriate knowledge and consent. Protect live telemetry with authentication, least-privilege rules and sensible retention. Do not rely on this dashboard as the sole safety measure.

## Phone GPS sharing and accessible voice alerts

The dashboard can use the **phone's own GPS** while the shoe sends obstacle distances over BLE:

1. Open the GitHub Pages dashboard on an Android phone in Chrome (HTTPS).
2. Sign in to Firebase with an account allowed to read/write `devices/smartshoe_001`.
3. Connect the shoe using **Connect SmartShoe BLE**. The website continues to receive the existing `front,left,right,lower` BLE distance packet; no ESP32 GPS module is needed for phone-based location.
4. Tap **Share phone live location** and allow the browser's location permission. The phone browser uses Geolocation API and writes `lat`, `lon`, `accuracy_m`, `source`, and `timestamp` to `devices/smartshoe_001/location` in Realtime Database. A parent dashboard signed into the same project can then read and show this location.
5. Tap **Enable voice alerts** once (a user action is required by browser audio policies). When a valid sensor reading reaches 30 cm or less, the browser speaks the direction and distance. Thresholds are 30, 20, 10, 8, 7, 6, 5, 4, 3, 2 and 1 cm. The browser's speech engine and phone media volume control loudness.

**Important limitations:** keep the phone with the person wearing the shoe; phone GPS locates the phone, not the shoe independently. Location sharing needs HTTPS, location permission, internet access and Firebase authentication/database rules that permit the signed-in user to write the location child path. Web Bluetooth is supported by compatible browsers such as Chrome on Android; iOS browser support is limited. Voice announcements need the page open and the browser active; this is a prototype feature, not a certified assistive or emergency system. Sensor distances are ultrasonic measurements, not object identification.
