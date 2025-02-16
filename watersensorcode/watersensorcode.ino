#include <OneWire.h>
#include <DallasTemperature.h>

const int DS18B20_PIN = 22;
const int TURBIDITY_PIN = A0;
const int HALLSENSOR_PIN = 2;  // Make sure this pin supports external interrupts

volatile int NbTopsFan = 0;
float Calc = 0;

OneWire oneWire(DS18B20_PIN);
DallasTemperature sensors(&oneWire);

void rpm() {
    NbTopsFan++;
}

void setup() {
    Serial.begin(9600);

    // Initialize temperature sensor
    sensors.begin();

    // Initialize flow sensor
    pinMode(HALLSENSOR_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(HALLSENSOR_PIN), rpm, RISING);
}

void loop() {
    // Read temperature
    sensors.requestTemperatures();
    float tempC = sensors.getTempCByIndex(0);
    
    // Read turbidity
    float turbidity = analogRead(TURBIDITY_PIN);
    
    // Read flow rate
    NbTopsFan = 0;  
    sei();  // Enable interrupts
    delay(1000);  // Measure for 1 second
    cli();  // Disable interrupts
    Calc = (NbTopsFan * 60.0 / 5.5);  // Convert to L/hour

    // Print results
    Serial.print("Turbidity: ");
    Serial.println(turbidity);

    if (tempC == -127.00) {
        Serial.println("Error: No DS18B20 sensor detected!");
    } else {
        Serial.print("Temperature: ");
        Serial.print(tempC);
        Serial.println(" °C");
    }

    Serial.print("Flow Rate: ");
    Serial.print(Calc);
    Serial.println(" L/hour");

    delay(1000);  // Delay before next reading
}
