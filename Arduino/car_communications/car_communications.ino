#include <Arduino.h>
#include <AFMotor.h>
#include "CommsBytes.h"
class CommsHandler {
  /*
  Communications handler.
  This class reads a series of bytes sent from the serial port and
  translates it into a relevant method call.

  All bytes are defined in CommsBytes.h
  */
  const static int bufferSize = 24;
  public: char commandBuffer[bufferSize];
  int bufferPosition = 0;
  public: bool activeMessage = false;
  bool nextCharEscaped = false;
  public: bool messageInBuffer = false;

  public: CommsHandler() {
    emptyBuffer();
  }

  public: void emptyBuffer() {
    for (size_t i = 0; i < bufferSize; i++) {
      commandBuffer[i] = 0;
    }
    bufferPosition = 0;
    activeMessage = false;
    nextCharEscaped = false;
    messageInBuffer = false;
  }
  public: bool readByte(char input) {
    /*receive a byte from the serial port and construct an escaped
    command buffer.

    returns true if byte received is appropriate.
    */

    if(not activeMessage){
      if(input == START) {
        activeMessage = true;
        return true;
      } else {
        return false;
      }
    }
    else { //If the message is currently ongoing
      if (nextCharEscaped) {
        input = input ^ ESC_XOR;
        nextCharEscaped = false;

      } else if(input == ESC) {
        nextCharEscaped = true;

      } else if(input == END) {
        messageInBuffer = true;
        activeMessage = false;
        bufferPosition = 0;
        return true;

      } else if(input == START) {
        emptyBuffer();
        activeMessage = true;
        return true;
      }


      commandBuffer[bufferPosition] = input;
      bufferPosition++;
    }
  }
  char getCheckSum() {
    char chksum = 0;
    for (int i = 0; i < bufferSize; i++) {
      chksum ^= commandBuffer[i];
    }
    return chksum;
  }
  public: bool sendOK() {
    Serial1.write(START);
    Serial1.write(2L);
    Serial1.write(R_OK);
    Serial1.write(getCheckSum());
    Serial1.write(END);
  }
  public: bool sendHeartBeat() {
    Serial1.write(START);
    Serial1.write(2L);
    Serial1.write(HEARTBEAT);
    Serial1.write(getCheckSum());
    Serial1.write(END);
  }
  public: bool sendHandShake(char handshake) {
    Serial1.write(START);
    Serial1.write(2L);
    Serial1.write(!handshake);
    Serial1.write(getCheckSum());
    Serial1.write(END);
  }
  public: bool sendError() {
    Serial1.write(START);
    Serial1.write(2L);
    Serial1.write(R_ERR);
    Serial1.write(getCheckSum());
    Serial1.write(END);
  }
  public: bool sendOutOfRange() {
    Serial1.write(START);
    Serial1.write(2L);
    Serial1.write(R_VAL_OOR);
    Serial1.write(getCheckSum());
    Serial1.write(END);
  }
  public: bool sendFunctionNA() {
    Serial1.write(START);
    Serial1.write(2L);
    Serial1.write(R_FUNC_NA);
    Serial1.write(getCheckSum());
    Serial1.write(END);
  }
  public: bool sendReqMalformed() {
    Serial1.write(START);
    Serial1.write(2L);
    Serial1.write(R_MAL_REQ);
    Serial1.write(getCheckSum());
    Serial1.write(END);
  }
};

class CarRunner {
  /*
  Stateful controller for the cars speed.
  The car has a serious issue with dead zone and hysteresis on the motors,
  and so this class gives the motors small bursts of speed if the desired speed
  is lower than the minimum continuous motor speed.
  */
  int counter = 0;
  const int counterPeriod = 1;  // period for updating counter. milliseconds. prefer power of 2, since it's used in division
  long lastCounterUpdate = 0;
  int threshold = 100;

  boolean run = true;  // flag for toggling operation
  boolean timeout = false;  // flag for timeout detection
  long timeout_time = 1000;  // milliseconds
  long lastCommand = 0;  // contains time for last received message

  int leftSpeed = 0;
  int rightSpeed = 0;

  AF_DCMotor* FR; // create motor #4, 1KHz pwm
  AF_DCMotor* FL; // create motor #3, 1KHz pwm
  AF_DCMotor* RR; // create motor #1, 2KHz pwm
  AF_DCMotor* RL; // create motor #2, 2KHz pwm

  public: CarRunner(){
    FR = new AF_DCMotor(1); // create motor #4, 1KHz pwm
    FL = new AF_DCMotor(2); // create motor #3, 1KHz pwm
    RR = new AF_DCMotor(4); // create motor #1, 2KHz pwm
    RL = new AF_DCMotor(3); // create motor #2, 2KHz pwm
    lastCommand = millis();
  }


  public: void runCar(){
    /*
    Main function for running the car.
    Increases a counter loop. If the counter is
    below the speed value, the actual output speed is set to the minimum
    functioning speed. The time the counter spends below the speed
    value is linear with the speed value, and so the speed actually achieved
    is still a linear function of the speed input.
    */
    uint8_t leftWheelOut_U = 2*abs(leftSpeed);
    uint8_t rightWheelOut_U = 2*abs(rightSpeed);


    counter++;
    if (counter > threshold){
      counter = 0;
    }

    if(abs(leftSpeed) < threshold){
      if(counter < leftSpeed)  {
        leftWheelOut_U = threshold;  // set speed to minimum functioning
      } else {
        leftWheelOut_U = 0;
      }
    } else leftWheelOut_U = (uint8_t)abs(leftSpeed);

    if(abs(rightSpeed) < threshold) {
      if(counter < rightSpeed)  {
        rightWheelOut_U = threshold;  // set speed to minimum functioning
      } else {
        rightWheelOut_U = 0;
      }
    } else {
      rightWheelOut_U = (uint8_t)abs(rightSpeed);
    }

    if(millis() > lastCommand + timeout_time){
      timeout = true;
    } else {
      timeout = false;
    }
    if (run and not timeout){

      FL->setSpeed(leftWheelOut_U);
      RL->setSpeed(leftWheelOut_U);
      FR->setSpeed(rightWheelOut_U);
      RR->setSpeed(rightWheelOut_U);
      if(leftSpeed > 0) {
        FL->run(FORWARD);
        RL->run(FORWARD);
        }
      else {
        FL->run(BACKWARD);
        RL->run(BACKWARD);
        }

     if(rightSpeed > 0) {
        FR->run(FORWARD);
        RR->run(FORWARD);
        }
     else {
        FR->run(BACKWARD);
        RR->run(BACKWARD);
    }

      /*
      FL->run(FORWARD);
      RL->run(FORWARD);
      FR->run(FORWARD);
      RR->run(FORWARD);
      */
    }
  }
  public: void setSpeed(int leftWheels, int rightWheels){
    /*
    Setter for motor speeds. Also updates timeout timer.
    */
    leftSpeed = leftWheels;
    rightSpeed = rightWheels;
    lastCommand = millis();
  }
};

int initialSpeed = 80;
CarRunner car = CarRunner();
CommsHandler comms = CommsHandler();

int incomingByte;
float pController;
int l_wheel = 0;
int r_wheel = 0;
int speed = 0;
int turnRate = 0;
signed int var = 0;
long lastCommandMillis = 0;
int timeout = 1000;
void setup()
{
  Serial1.begin(115200);          // Rpi port
  Serial.begin(115200);           // Arduino port
  car.setSpeed(0,0);
}

void loop()
{
    while (Serial1.available()> 0){
      byte data = Serial1.read();

      if(data != 0) {
        Serial.print("got ");
        Serial.println(data);
      }
      comms.readByte(data);
      if(comms.messageInBuffer) {
        break;
      }
    }
    const int CMD_GROUP_BYTE = 4;
    const int CMD_BYTE = 5;
    if(comms.messageInBuffer) {
      lastCommandMillis = millis();
      if(comms.commandBuffer[CMD_GROUP_BYTE] == CMD_STATUS) {
        if(comms.commandBuffer[CMD_BYTE] == HEARTBEAT) {
          comms.sendHeartBeat();
        } else if(comms.commandBuffer[CMD_BYTE] == HANDSHAKE) {
          comms.sendHandShake(comms.commandBuffer[CMD_BYTE+1]);
        } else if(comms.commandBuffer[CMD_BYTE] == ASK_STATUS) {
          comms.sendFunctionNA();
        } else {
          comms.sendReqMalformed();
        }

      } else if(comms.commandBuffer[CMD_GROUP_BYTE] == CMD_SET_PARAMS) {
        if(comms.commandBuffer[CMD_BYTE] == SET_MOT_THR) {
          comms.sendFunctionNA();
        } else if(comms.commandBuffer[CMD_BYTE] == DO_CALIB_GYRO) {
          comms.sendFunctionNA();
        } else {
          comms.sendReqMalformed();
        }

      } else if(comms.commandBuffer[CMD_GROUP_BYTE] == CMD_SPEED) {
        if(comms.commandBuffer[CMD_BYTE] == WHEEL_SPD) {
          r_wheel = (int8_t) comms.commandBuffer[CMD_BYTE+1];
          l_wheel = (int8_t) comms.commandBuffer[3];
          comms.sendOK();

        } else if(comms.commandBuffer[CMD_BYTE] == CAR_SPD) {
          speed = (int) comms.commandBuffer[CMD_BYTE+1];
          r_wheel = speed + turnRate;
          l_wheel = speed - turnRate;
          comms.sendOK();

        } else if(comms.commandBuffer[CMD_BYTE] == TURN_SPD) {
          turnRate = (int) comms.commandBuffer[CMD_BYTE+1];
          r_wheel = speed + turnRate;
          l_wheel = speed - turnRate;
          comms.sendOK();

        } else {
          comms.sendReqMalformed();
        }

      } else if(comms.commandBuffer[CMD_GROUP_BYTE] == CMD_SPEED_CL) {
        if(comms.commandBuffer[CMD_BYTE] == DIST_CL) {
          comms.sendFunctionNA();
        } else if(comms.commandBuffer[CMD_BYTE] == TURN_CL) {
          comms.sendFunctionNA();
        } else if(comms.commandBuffer[CMD_BYTE] == TURN_ABS_CL) {
          comms.sendFunctionNA();
        } else {
          comms.sendReqMalformed();
        }

      } else if(comms.commandBuffer[CMD_GROUP_BYTE] == REQ_SENS) {
        if(comms.commandBuffer[CMD_BYTE] == REQ_COMPASS) {
          comms.sendFunctionNA();
        } else if(comms.commandBuffer[CMD_BYTE] == REQ_ACC) {
          comms.sendFunctionNA();
        } else if(comms.commandBuffer[CMD_BYTE] == REQ_GYRO) {
          comms.sendFunctionNA();
        } else {
          comms.sendReqMalformed();
        }
      } else {
        comms.sendReqMalformed();
      }
      comms.messageInBuffer = false;
      comms.emptyBuffer();
    }
    if (millis() - lastCommandMillis > timeout)
    {
      car.setSpeed(0,0);
      //Serial.println("no signal from Rpi! \n");
    } else {

       //Serial.println(incomingByte);

       int leftW  = constrain(l_wheel,  -255, 255);
       int rightW = constrain(r_wheel, -255, 255);
       if (false){
       Serial.print("l_wheel: ");
       Serial.println(leftW);
       Serial.print("r_wheel ");
       Serial.println(rightW);
       }
       car.setSpeed(leftW, rightW);
       //car.setSpeed(0, 0);
     }
     car.runCar();
}
