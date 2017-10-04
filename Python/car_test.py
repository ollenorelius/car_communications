"""Quick and dirty script to test function of communications."""
import car_connection as cc
import comms_bytes as cb
import time
car = cc.CarConnection()
time.sleep(2)
car.send_message(group=cb.CMD_SPEED, command=cb.CAR_SPD, data=[0x81])
car.send_message(group=cb.CMD_SPEED, command=cb.TURN_SPD, data=[0x11])
time.sleep(2)
car.send_message(group=cb.CMD_SPEED, command=cb.CAR_SPD, data=[0x00])
car.send_message(group=cb.CMD_SPEED, command=cb.TURN_SPD, data=[0x00])
time.sleep(1)
