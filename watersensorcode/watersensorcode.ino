void setup() {
    Serial.begin(9600);  // Start Serial Monitor at 115200 baud
}

void loop() {
    int analogValue = analogRead(15);  // Read analog value from GPIO15
    Serial.println(analogValue);       // Print to Serial Monitor
    delay(500);  // Wait 500ms to avoid flooding output
}
