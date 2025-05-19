#include <Arduino.h>

int relay_1 = 4;
int relay_2 = 7;
int relay_3 = 8;
int relay_4 = 12;
String serialInput;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  pinMode(relay_1, OUTPUT);
  pinMode(relay_2, OUTPUT);
  pinMode(relay_3, OUTPUT);
  pinMode(relay_4, OUTPUT);

}

void on() {
  digitalWrite(relay_3, HIGH);
  digitalWrite(relay_4, HIGH);
}

void off() {
  digitalWrite(relay_4, LOW);
  delay(500);
  digitalWrite(relay_3, LOW);
}

void loop() {

  while (Serial.available() > 0) {
    serialInput = Serial.readStringUntil('\n'); // Read input until newline
    //if the incoming character is a newline, process the string
    Serial.println(serialInput);
    if(serialInput == "ON"){
      Serial.println("TOOL ON");
      on();
    }
    else if (serialInput == "OFF"){
      Serial.println("TOOL OFF");
      off();
    }
    serialInput = ""; //clear the input
    }
  }
