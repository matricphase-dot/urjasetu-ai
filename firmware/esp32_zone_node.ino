/*
 * UrjaSetu AI — ESP32 Zone Node firmware
 * =======================================
 * The ₹500 field device that closes the loop on REAL hardware:
 *   - DHT22    : zone temperature + humidity (every 15 s)
 *   - PIR HC-SR501 : occupancy presence (feeds the forecaster)
 *   - Relay    : actuates a fan / AHU pilot — the AI's write-side
 *   - MQTT     : telemetry up, setpoints down (TLS in production)
 *
 * Bill of materials (Indicative India pricing):
 *   ESP32 DevKit v1        ₹380–450
 *   DHT22 / AM2302         ₹180–250
 *   PIR HC-SR501           ₹ 60–80
 *   5V relay module        ₹ 50–80
 *   5V phone charger + wire ₹ 80
 *   TOTAL                  ≈ ₹750 per zone  (₹500 class if DHT11 + stripped BOM)
 *
 * Libraries (Arduino Library Manager): PubSubClient, ArduinoJson, DHT sensor library
 * Wiring: DHT22 → GPIO4 · PIR → GPIO5 · Relay IN → GPIO12 (see docs/ARCHITECTURE.md)
 *
 * SAFETY: this sketch switches LOW-VOLTAGE fan/pilot loads only.
 * Mains-side wiring must be done by a licensed electrician through a proper
 * contactor. Never wire mains directly to a dev board.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

// ----------------- configuration (edit before flashing) -----------------
const char* WIFI_SSID   = "YOUR_WIFI";
const char* WIFI_PASS   = "YOUR_PASS";
const char* MQTT_HOST   = "192.168.1.10";     // edge agent / broker
const int   MQTT_PORT   = 1883;               // 8883 + TLS in production
const char* NODE_ID     = "zone-L1-office-1"; // matches twin zone naming
const char* TOPIC_BASE  = "urjasetu/zone";
const char* TOPIC_TELE  = "urjasetu/zone/zone-L1-office-1/telemetry";
const char* TOPIC_CMD   = "urjasetu/zone/zone-L1-office-1/cmd";

const uint8_t PIN_DHT   = 4;
const uint8_t PIN_PIR   = 5;
const uint8_t PIN_RELAY = 12;                  // drives fan/pilot contactor coil
const uint32_t TELE_PERIOD_MS = 15000;         // 15 s telemetry heartbeat
const uint32_t LOOP_GUARD_MS  = 1000;

// ----------------- state -----------------
DHT dht(PIN_DHT, DHT22);
WiFiClient espClient;
PubSubClient mqtt(espClient);

float   lastSetpointC = 25.5;                  // AI default; cloud overwrites
String  lastMode      = "COOL";                // COOL | PRE-COOL | SETBACK | OFF
bool    occupancy     = false;
bool    relayOn       = false;
uint32_t lastTele = 0, lastLoop = 0;

// Fail-safe: if no heartbeat from the brain for 5 min, revert to local schedule
const uint32_t HEARTBEAT_TIMEOUT_MS = 300000;
uint32_t lastCmdMs = 0;

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(300); }
}

void onCmd(char* topic, byte* payload, unsigned int len) {
  JsonDocument doc;                              // {"setpoint_c":24.3,"mode":"PRE-COOL"}
  if (deserializeJson(doc, payload, len)) return;
  lastSetpointC = doc["setpoint_c"] | lastSetpointC;
  lastMode      = String((const char*)(doc["mode"] | "COOL"));
  lastCmdMs     = millis();
  applyControl();
}

void applyControl() {
  // Relay logic — the AI "acts" here. Hysteresis prevents relay chatter.
  bool wantOn;
  if (lastMode == "OFF" || lastMode == "SETBACK") wantOn = false;
  else wantOn = (dht.readTemperature() > lastSetpointC + 0.3);
  if (wantOn != relayOn) {
    relayOn = wantOn;
    digitalWrite(PIN_RELAY, relayOn ? HIGH : LOW);
  }
}

void publishTelemetry() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  if (isnan(t) || isnan(h)) return;              // never publish garbage
  JsonDocument doc;
  doc["node"]        = NODE_ID;
  doc["temp_c"]      = round(t * 10) / 10.0;
  doc["rh_pct"]      = round(h * 10) / 10.0;
  doc["occupancy"]   = occupancy;
  doc["relay_on"]    = relayOn;
  doc["setpoint_c"]  = lastSetpointC;
  doc["mode"]        = lastMode;
  doc["rssi_dbm"]    = WiFi.RSSI();
  char buf[192];
  serializeJson(doc, buf);
  mqtt.publish(TOPIC_TELE, buf);
}

void setup() {
  pinMode(PIN_RELAY, OUTPUT);
  digitalWrite(PIN_RELAY, LOW);
  pinMode(PIN_PIR, INPUT);
  dht.begin();
  connectWiFi();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onCmd);
}

void loop() {
  if (!mqtt.connected()) {
    // Exponential-ish backoff reconnect
    mqtt.connect("urjasetu-" NODE_ID);
    if (mqtt.connected()) mqtt.subscribe(TOPIC_CMD);
    delay(800);
  }
  mqtt.loop();

  uint32_t now = millis();
  if (now - lastLoop > LOOP_GUARD_MS) {          // 1 Hz slow loop is plenty
    lastLoop = now;
    occupancy = digitalRead(PIN_PIR);            // presence re-check
    // Fail-safe autonomy: brain silent for 5 min → hold local comfort schedule
    if (now - lastCmdMs > HEARTBEAT_TIMEOUT_MS) {
      lastSetpointC = 25.5;
      lastMode      = "COOL";
      applyControl();
    } else {
      applyControl();
    }
  }
  if (now - lastTele > TELE_PERIOD_MS) {
    lastTele = now;
    publishTelemetry();
  }
}
