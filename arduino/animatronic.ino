#include <Servo.h>
Servo myServo;

const int servoPin = 8;

void setup() {
  myServo.attach(servoPin);
  Serial.begin(9600);

  myServo.write(90);
}

void loop() {
  String data = Serial.readStringUntil(',');

  if (data == "servo") {
    int rotation = Serial.readStringUntil('\n').toInt();
    myServo.write(rotation);
  }
}
