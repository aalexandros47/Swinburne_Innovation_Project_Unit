#define STEP_PIN_SWAB D1
#define DIR_PIN_SWAB D0
#define STEP_PIN_OSC D3
#define DIR_PIN_OSC D2
#define STEP_PIN_ROT D5
#define DIR_PIN_ROT D4
#define STEP_PIN_PITCH D7
#define DIR_PIN_PITCH D6

#define ROT_ON D10
#define SWAB_ON D9
#define OSC_ON D8

void setup() {
  pinMode(STEP_PIN_SWAB, OUTPUT);
  pinMode(DIR_PIN_SWAB, OUTPUT);
  pinMode(STEP_PIN_OSC, OUTPUT);
  pinMode(DIR_PIN_OSC, OUTPUT);
  pinMode(STEP_PIN_ROT, OUTPUT);
  pinMode(DIR_PIN_ROT, OUTPUT);
  pinMode(STEP_PIN_PITCH, OUTPUT);
  pinMode(DIR_PIN_PITCH, OUTPUT);
  pinMode(ROT_ON, OUTPUT);
  pinMode(SWAB_ON, OUTPUT);
  pinMode(OSC_ON, OUTPUT);

  digitalWrite(DIR_PIN_SWAB, HIGH);  // Set direction
  digitalWrite(DIR_PIN_OSC, LOW);  // Set direction
  digitalWrite(DIR_PIN_ROT, LOW);  // Set direction
  digitalWrite(DIR_PIN_PITCH, LOW);  // Set direction
  digitalWrite(OSC_ON, HIGH);
  digitalWrite(SWAB_ON, HIGH);
  digitalWrite(ROT_ON, LOW);
}

void loop() {

  digitalWrite(STEP_PIN_OSC, HIGH);
  delayMicroseconds(800);   // Minimum pulse width (~1 µs required)
  digitalWrite(STEP_PIN_OSC, LOW);
  delayMicroseconds(800);
  
  // Move ONE step
  digitalWrite(STEP_PIN_SWAB, HIGH);
  delayMicroseconds(800);   // Minimum pulse width (~1 µs required)
  digitalWrite(STEP_PIN_SWAB, LOW);
  delayMicroseconds(800);
  
  digitalWrite(STEP_PIN_ROT, HIGH);
  delayMicroseconds(800);   // Minimum pulse width (~1 µs required)
  digitalWrite(STEP_PIN_ROT, LOW);
  delayMicroseconds(800);

  digitalWrite(STEP_PIN_PITCH, HIGH);
  delayMicroseconds(800);   // Minimum pulse width (~1 µs required)
  digitalWrite(STEP_PIN_PITCH, LOW);
  delayMicroseconds(800);
  
  delay(100);  // Wait 1 second before next step
}
