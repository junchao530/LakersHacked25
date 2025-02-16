#include <OneWire.h>
#include <DallasTemperature.h>

const int DS18B20_PIN = 22;
OneWire oneWire(DS18B20_PIN);
DallasTemperature sensors(&oneWire);

void setup() {
    Serial.begin(9600);
    sensors.begin();
}

void loop() {
    sensors.requestTemperatures();
    float tempC = sensors.getTempCByIndex(0);

    if (tempC == -127.00) {
        Serial.println("Error: No DS18B20 sensor detected!");
    } else {
        Serial.print("Temperature: ");
        Serial.print(tempC);
        Serial.println(" °C");
    }

    delay(1000);
}