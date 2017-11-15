"""Quick and dirty script to test function of communications."""
import autonomous.car_controller as cc
import time

car = cc.CarController()
time.sleep(2)
car.set_speed(100)
print("Going forward at 100")
time.sleep(1)
car.set_speed(0)
print("Stopping")
time.sleep(1)
car.set_turnrate(100)
print("Turning at 100")
time.sleep(1)
car.set_turnrate(0)
print("Stopping")
time.sleep(1)
