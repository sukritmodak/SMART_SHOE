/*
  SMART SHOE - Classic Bluetooth SPP firmware
  Board: original ESP32 / ESP32-D0WD-V3 (not ESP32-S3)
  CSV protocol: front,left,right,lower followed by newline.
  HC-SR04 ECHO must be reduced to 3.3V with a voltage divider.
*/
#include <Arduino.h>
#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error "Classic Bluetooth is unavailable. Select an original ESP32 board, not ESP32-S3."
#endif

BluetoothSerial SerialBT;

// Original sensor pin mapping - retained
#define FRONT_TRIG 5
#define FRONT_ECHO 34
#define LEFT_TRIG 18
#define LEFT_ECHO 35
#define RIGHT_TRIG 19
#define RIGHT_ECHO 32
#define LOWER_TRIG 21
#define LOWER_ECHO 33
#define BUZZER_PIN 4

const float INVALID_DISTANCE = 999.0f;
const float ALERT_DISTANCE_CM = 80.0f;
const uint32_t ECHO_TIMEOUT_US = 30000UL;
const uint32_t SENSOR_GAP_MS = 60;
const uint32_t BT_SEND_INTERVAL_MS = 500;
const uint32_t SERIAL_PRINT_INTERVAL_MS = 1000;

float frontDistance = INVALID_DISTANCE;
float leftDistance = INVALID_DISTANCE;
float rightDistance = INVALID_DISTANCE;
float lowerDistance = INVALID_DISTANCE;
uint32_t lastBtSend = 0;
uint32_t lastSerialPrint = 0;

float readDistance(uint8_t trigPin, uint8_t echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(3);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  const uint32_t duration = pulseIn(echoPin, HIGH, ECHO_TIMEOUT_US);
  if (duration == 0) return INVALID_DISTANCE;

  const float cm = (duration * 0.0343f) / 2.0f;
  if (cm < 2.0f || cm > 400.0f) return INVALID_DISTANCE;
  return cm;
}

void readAllSensors() {
  frontDistance = readDistance(FRONT_TRIG, FRONT_ECHO);
  delay(SENSOR_GAP_MS);
  leftDistance = readDistance(LEFT_TRIG, LEFT_ECHO);
  delay(SENSOR_GAP_MS);
  rightDistance = readDistance(RIGHT_TRIG, RIGHT_ECHO);
  delay(SENSOR_GAP_MS);
  lowerDistance = readDistance(LOWER_TRIG, LOWER_ECHO);
  delay(SENSOR_GAP_MS);
}

void updateBuzzer() {
  const bool obstacle =
    frontDistance <= ALERT_DISTANCE_CM ||
    leftDistance <= ALERT_DISTANCE_CM ||
    rightDistance <= ALERT_DISTANCE_CM ||
    lowerDistance <= ALERT_DISTANCE_CM;
  // Assumes an active-HIGH active buzzer module.
  digitalWrite(BUZZER_PIN, obstacle ? HIGH : LOW);
}

void sendClassicBluetoothData() {
  if (!SerialBT.hasClient()) return;
  SerialBT.printf("%.1f,%.1f,%.1f,%.1f\n",
                  frontDistance, leftDistance,
                  rightDistance, lowerDistance);
}

void printDebugData() {
  Serial.printf("Front %.1f cm | Left %.1f cm | Right %.1f cm | Lower %.1f cm | SPP: %s\n",
                frontDistance, leftDistance, rightDistance, lowerDistance,
                SerialBT.hasClient() ? "connected" : "waiting");
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(FRONT_TRIG, OUTPUT); pinMode(FRONT_ECHO, INPUT);
  pinMode(LEFT_TRIG, OUTPUT);  pinMode(LEFT_ECHO, INPUT);
  pinMode(RIGHT_TRIG, OUTPUT); pinMode(RIGHT_ECHO, INPUT);
  pinMode(LOWER_TRIG, OUTPUT); pinMode(LOWER_ECHO, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  digitalWrite(FRONT_TRIG, LOW);
  digitalWrite(LEFT_TRIG, LOW);
  digitalWrite(RIGHT_TRIG, LOW);
  digitalWrite(LOWER_TRIG, LOW);

  Serial.println("\nSMART SHOE - CLASSIC BLUETOOTH SPP");
  if (!SerialBT.begin("SmartShoe")) {
    Serial.println("ERROR: Classic Bluetooth SPP could not start.");
    while (true) { digitalWrite(BUZZER_PIN, LOW); delay(1000); }
  }
  Serial.println("SPP started. Pair Windows with: SmartShoe");
  Serial.println("Packet order: front,left,right,lower");
}

void loop() {
  readAllSensors();
  updateBuzzer();

  const uint32_t now = millis();
  if (now - lastBtSend >= BT_SEND_INTERVAL_MS) {
    lastBtSend = now;
    sendClassicBluetoothData();
  }
  if (now - lastSerialPrint >= SERIAL_PRINT_INTERVAL_MS) {
    lastSerialPrint = now;
    printDebugData();
  }
}
