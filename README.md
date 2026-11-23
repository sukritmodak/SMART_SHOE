# SMART SHOE — Parent Safety Dashboard

A responsive GitHub Pages dashboard for the SMART SHOE ESP32-S3 prototype.

## Website

After GitHub Pages is enabled, open:

https://sukritmodak.github.io/SMART_SHOE/

In **Repository → Settings → Pages**, select **Deploy from a branch**, branch **main**, folder **/(root)**, then Save. The site is static HTML; no build command is required.

## What this version connects to

- **Firebase Realtime Database over Wi-Fi:** signs in through Firebase Email/Password Authentication in the browser, then reads the latest device record every 2 seconds.
- **ESP32-S3 BLE:** uses the custom service and characteristic UUIDs from the current ESP32 sketch and parses the four comma-separated distance values.
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
2. Create/confirm the account that the ESP32 firmware uses.
3. Create a **Realtime Database** in the same Firebase project and confirm its database URL matches the firmware.
4. Configure Realtime Database Rules so unauthenticated visitors cannot read or write device data. The dashboard signs in and sends its Firebase ID token when reading.
5. Enter the Firebase email and password into the dashboard at runtime. The website does not store the password in its source code.

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

## ESP32-S3 BLE protocol

The website now uses the exact custom UUIDs from the current firmware:

- Service: `12345678-1234-1234-1234-123456789000`
- Notify characteristic: `12345678-1234-1234-1234-123456789001`

The current firmware notification is comma-separated in this order:

```text
front,left,right,lower
```

Example:

```text
45.2,30.5,80.0,25.4
```

The website parses each BLE notification directly; it does not require Nordic UART UUIDs or newline-delimited JSON. Use a Web Bluetooth-compatible browser (for example Chrome or Edge) on HTTPS, and allow Bluetooth access when prompted.

## Location limitation

The current ESP32 firmware uploads only four ultrasonic distances and device status. It does **not** send GPS coordinates, step count, accelerometer data or battery level. Therefore this dashboard will not invent a child location or show a fake live route. The map will show a marker only after GPS fields are added to the device/cloud data. A GPS source is required on the shoe or a paired child-side phone, and its coordinates must be uploaded to Firebase.

## Troubleshooting

- **Firebase sign-in failed:** check Email/Password Authentication, account credentials, API key/project, and browser network access.
- **Firebase permission denied:** check that Realtime Database exists and its Rules allow authenticated reads for `devices/smartshoe_001`.
- **No device record:** confirm the ESP32 has successfully authenticated and uploaded to the same database URL and device ID.
- **BLE device not listed:** ensure the ESP32 is powered, advertising, and using the service UUID above. Use HTTPS and a supported browser.
- **BLE connects but values do not change:** verify the characteristic UUID and that notifications contain four comma-separated numeric values in front,left,right,lower order.

## Safety and privacy

This is an academic prototype, not a certified child-safety or emergency-response system. Use location tracking transparently with appropriate knowledge and consent. Protect live telemetry with authentication, least-privilege rules and sensible retention. Do not rely on this dashboard as the sole safety measure.
