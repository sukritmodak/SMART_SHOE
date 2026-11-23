# SMART SHOE — Parent Safety Dashboard

A responsive web dashboard for a smart-shoe prototype. It is designed to display a child's shared GPS position, route, movement, step count, obstacle range readings, accelerometer data and battery status.

## Live website

After GitHub Pages deployment completes, the site should be available at:
https://sukritmodak.github.io/SMART_SHOE/

## Current capabilities

- Responsive parent dashboard for phone and desktop
- OpenStreetMap location map and breadcrumb route
- BLE UART connection in supported browsers (Nordic UART Service UUID)
- Wi-Fi/cloud JSON polling endpoint (HTTPS, CORS required)
- Phone GPS permission flow
- Front/left/right/rear distance visualization and proximity warnings
- Clearly labelled simulated demo mode

## Important hardware integration notes

**This repository was empty when this website was added.** The website therefore uses an adaptable JSON interface rather than claiming to know the shoe firmware packet format.

### Suggested telemetry JSON

Send one JSON object per line over BLE, or expose the latest JSON object from your HTTPS endpoint:

```json
{
  "device_id": "smart-shoe-01",
  "lat": 28.6139,
  "lon": 77.2090,
  "activity": "Walking",
  "steps": 1250,
  "front_cm": 42,
  "left_cm": 85,
  "right_cm": 110,
  "rear_cm": 140,
  "accel": {"x": 0.12, "y": -0.08, "z": 9.78},
  "battery_percent": 88
}
```

Accepted location aliases include latitude/longitude, lng, location.lat/location.lon and gps.lat/gps.lon. Distance aliases include distance_front, frontDistance and distances.front (and corresponding left/right/rear fields).

### Bluetooth

The browser BLE connector currently expects the Nordic UART Service:
- Service: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- Notify characteristic: `6e400003-b5a3-f393-e0a9-e50e24dcca9e`

It expects newline-delimited UTF-8 JSON. If the ESP32 uses a different BLE service/characteristic or Bluetooth Classic (for example HC-05 SPP), the firmware/protocol or a companion phone bridge must be adapted. Web Bluetooth does not support every Bluetooth Classic serial module.

### Wi-Fi and remote parent access

The dashboard polls an HTTPS JSON URL every 2 seconds. The endpoint must return the latest device object and allow browser CORS requests. For a real remote parent dashboard, the shoe/child phone must upload telemetry to a cloud service (for example a properly secured Firebase Realtime Database or your own API). The parent dashboard then reads that shared record. A GitHub Pages static site cannot itself receive or relay live ESP32 data.

Do not put private API keys, database admin credentials or unrestricted write rules in this public repository. Use authentication and per-device access rules.

### GPS and location accuracy

Phone GPS sharing uses the browser's geolocation permission on the device where the page is open. For parents to see a child's location remotely, the child's phone/device must share the location to the configured cloud endpoint. Wi-Fi network visibility by itself does not provide precise GPS coordinates.

### Obstacle mapping limitations

The radar-style display plots the range values by sensor direction. A real spatial map requires known sensor orientation and multiple directional sensors or angle-tagged LiDAR/radar samples. A single distance reading only reports range along its sensing direction; it cannot reconstruct an object's full shape or position.

## Deployment

GitHub Actions deploys the static site to GitHub Pages on pushes to `main`. In GitHub, open **Settings → Pages** and select **GitHub Actions** as the build and deployment source if it is not already selected. The workflow run is visible in the Actions tab.

## Safety and privacy

This is an academic prototype, not a certified child-safety or emergency-response system. Use location tracking transparently with the child's and guardian's knowledge and consent. Protect all live data with authentication, limit retention, and never rely on this dashboard as the sole safety measure.
