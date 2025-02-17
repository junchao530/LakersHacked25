// HACKED 2025!!

// library imports
#include <SoftwareSerial.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <LiquidCrystal.h>
#include <RTClib.h>

// define constants
#define FLOW_SENSOR 12
#define TEMP_SENSOR 13
#define TURBIDITY_SENSOR A0
#define RX 10
#define TX 11
#define BUTTON_PIN 2
#define DEBOUNCE_DELAY 50 // Debounce time in milliseconds

// create objects
SoftwareSerial bluetoothSerial(RX, TX);
LiquidCrystal lcd(52, 50, 53, 51, 49, 47, 45, 43, 41, 39);
OneWire oneWire(TEMP_SENSOR);
DallasTemperature temp_sensor(&oneWire);
RTC_DS1307 rtc;

char daysOfTheWeek[7][12] = {
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday"
};

//instantiate variables
int buttonState = 0;
volatile bool buttonPressed = false;
volatile unsigned long lastDebounceTime = 0;

char buffer[16];

unsigned long Htime;
unsigned long Ltime;
unsigned long Ttime;
float flow_rate;
float frequency;

float tempC;

long turbidity_raw, water_quality_score;
int BluetoothData;

void buttonISR() {
  // Serial.println("tanveer");
  unsigned long currentTime = millis();
  if ((currentTime - lastDebounceTime) > DEBOUNCE_DELAY) {
    buttonPressed = true;
    lastDebounceTime = currentTime;
  }
}

void run_flow_sensor() {
  // Calculations for flow sensor
  Htime = pulseIn(FLOW_SENSOR, HIGH);
  Ltime = pulseIn(FLOW_SENSOR, LOW);
  Ttime = Htime + Ltime;

  if (Ttime > 0) {
    frequency = 1000000.0 / Ttime;
    flow_rate = frequency / 5.5;
  } else {
    frequency = 0;
    flow_rate = 0;  // No flow detected
  }

}

void run_temp_sensor() {
  // Read temperature
  temp_sensor.requestTemperatures();
  tempC = temp_sensor.getTempCByIndex(0);

}

void run_turbidity_sensor() {
  turbidity_raw = analogRead(TURBIDITY_SENSOR);
  water_quality_score = map(turbidity_raw, 0, 999, 0, 100);

  water_quality_score = constrain(water_quality_score, 0, 100);

}

void push_data() {
  // Push flow data
  bluetoothSerial.print("Flow: ");
  bluetoothSerial.print(flow_rate);
  // bluetoothSerial.print(" L/min");
  bluetoothSerial.print(";");

  // Push temp data
  if (tempC == -127.00) {
      bluetoothSerial.print("Error: No DS18B20 sensor detected!;");
  } else {
      bluetoothSerial.print("Temperature: ");
      bluetoothSerial.print(tempC);
      // bluetoothSerial.print(" C");
      bluetoothSerial.print(";");
  }

  // Push turbidity data
  bluetoothSerial.print("Turbidity: ");
  bluetoothSerial.print(water_quality_score);
  bluetoothSerial.println("");

}

void print_lcd(){
  lcd.clear();
  switch(buttonState) {
    case 0:
      lcd.home();
      lcd.print("Flow Rate:");

      sprintf(buffer, "%d L/min", (int) flow_rate);
      lcd.setCursor(0, 1);
      lcd.print(buffer);
      break;

    case 1:
      lcd.home();
      lcd.print("Water Quality:");

      sprintf(buffer, "%d/100", water_quality_score);
      lcd.setCursor(0, 1);
      lcd.print(buffer);
      break;

    case 2:
      lcd.home();
      lcd.print("Temperature:");

      sprintf(buffer, "%d C ", (int) tempC);
      lcd.setCursor(0, 1);
      lcd.print(buffer);
      break;
    
    default:
      break;
  }

}

void generate_datetime() {
  DateTime now = rtc.now();

  // Ensure proper formatting with zero-padding
  bluetoothSerial.print("Date: ");
  bluetoothSerial.print(now.year());
  bluetoothSerial.print('-');
  if (now.month() < 10) bluetoothSerial.print('0'); 
  bluetoothSerial.print(now.month());
  bluetoothSerial.print('-');
  if (now.day() < 10) bluetoothSerial.print('0'); 
  bluetoothSerial.print(now.day());
  bluetoothSerial.print(' '); // Space between date and time

  if (now.hour() < 10) bluetoothSerial.print('0'); 
  bluetoothSerial.print(now.hour());
  bluetoothSerial.print('-');
  if (now.minute() < 10) bluetoothSerial.print('0'); 
  bluetoothSerial.print(now.minute());
  bluetoothSerial.print('-');
  if (now.second() < 10) bluetoothSerial.print('0'); 
  bluetoothSerial.print(now.second()); // Use println for newline
  
  bluetoothSerial.print(";");
}

void setup() {
  // Instantiate sensors
  pinMode(FLOW_SENSOR, INPUT);

  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(0, buttonISR, CHANGE);

  temp_sensor.begin();
  lcd.begin(16,2);
  lcd.clear();

  // Start bluetooth serial connection
  bluetoothSerial.begin(9600);
  bluetoothSerial.println("Device ON");
  Serial.begin(9600);

	// Setup RTC module
	if (! rtc.begin()) {
		bluetoothSerial.println("Couldn't find RTC");
		bluetoothSerial.flush();
		while(1);
	}

  rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));	

}

void loop() {
  if (buttonPressed) {
    buttonPressed = false;

    buttonState = (buttonState + 1) %3; // limit it from 0 to 2
  }
		
  run_flow_sensor();

  run_temp_sensor();

  run_turbidity_sensor();

  print_lcd();

	generate_datetime();	

  push_data();

  delay(100);// prepare for next data ...
}
