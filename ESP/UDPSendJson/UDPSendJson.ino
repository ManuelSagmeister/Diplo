#include <WiFi.h>
#include <WiFiUdp.h>
#include <SPI.h>
#include "link.h"
#include "DW1000Ranging.h"
#include <ArduinoJson.h>

#define SPI_SCK 18
#define SPI_MISO 19
#define SPI_MOSI 23
#define DW_CS 4

#define tag_MAC "1F:00:22:EoA:82:60:3B:9C"

//static ip
IPAddress local_IP(192, 168, 56, 151);
IPAddress gateway(192, 168, 56, 97);
IPAddress subnet(255, 255, 255, 0);

// connection pins
const uint8_t PIN_RST = 27; // reset pin
const uint8_t PIN_IRQ = 34; // irq pin
const uint8_t PIN_SS = 4;   // spi select pin

const char *ssid = "NOT YOURS";
const char *password = "xzzza50866";
const char *host = "192.168.56.147";
uint16_t portNum = 50000;

WiFiUDP udp;
struct MyLink *uwb_data;
unsigned long runtime = 0 ;
unsigned long updateInterval = 1000;


void setup() {
  Serial.begin(115200);

  if (WiFi.config(local_IP, gateway, subnet) == false) {
    Serial.println("Configuration failed.");
  }

  //init the configuration
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  DW1000Ranging.initCommunication(PIN_RST, PIN_SS, PIN_IRQ); //Reset, CS, IRQ pin
  //define the sketch as anchor. It will be great to dynamically change the type of module
  DW1000Ranging.attachNewRange(newRange);
  DW1000Ranging.attachNewDevice(newDevice);
  DW1000Ranging.attachInactiveDevice(inactiveDevice);
  //we start the module as a tag
  DW1000Ranging.startAsTag(tag_MAC, DW1000.MODE_LONGDATA_RANGE_LOWPOWER);
  uwb_data = init_link();

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(F("Connected"));
  Serial.print(F("IP Address:"));
  Serial.println(WiFi.localIP());

  delay(500);

  udp.begin(50000);

  Serial.println("SETUP COMPLETE");
}

void loop() {
  DW1000Ranging.loop();
  if ((millis() - runtime) > updateInterval) {
    // Create the JSON document describing the array of links
    send_json(uwb_data);
    // Update the timestamp
    runtime = millis();
  }
}

void send_json(struct MyLink *p) {

  StaticJsonDocument<500> doc;

  doc["tagMac"] = tag_MAC;

  // Create the array of links
  JsonArray links = doc.createNestedArray("links");
  struct MyLink *temp = p;
  while (temp->next != NULL) {
    temp = temp->next;
    JsonObject obj1 = links.createNestedObject();
    obj1["anchor"] = temp->anchor_addr;
    char range[5];
    sprintf(range, "%.2f", temp->range[0]);
    obj1["range"] = range;
  }

  serializeJson(doc, Serial);
  Serial.println("");
  //Serial.println(doc);

  udp.beginPacket(host, portNum);
  serializeJson(doc, udp);
  udp.println();
  udp.endPacket();
  
}

void newRange(){
  update_link(uwb_data, DW1000Ranging.getDistantDevice()->getShortAddress(), DW1000Ranging.getDistantDevice()->getRange(), DW1000Ranging.getDistantDevice()->getRXPower());
}

void newDevice(DW1000Device *device){
  add_link(uwb_data, device->getShortAddress());
}


void inactiveDevice(DW1000Device *device){
  delete_link(uwb_data, device->getShortAddress());
}
