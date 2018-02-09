import sys
import zmq
from matplotlib import pyplot as plt
import matplotlib.image as mpimg
import matplotlib.animation as animation
import matplotlib.cm as cm
from collections import deque
import numpy as np
import io
from PIL import Image
from autonomous.car_controller import CarController

car = CarController(address='192.168.150.149')
N = 150
r = 2 * np.random.rand(N)
theta = 2 * np.pi * np.random.rand(N)
area = 200 * r**2
colors = theta
data_queue = deque(maxlen=500)
fig = plt.figure()
plt.ion()

ax = fig.add_subplot(121, projection="polar")
ax2 = fig.add_subplot(122)


data = car.get_lidar()
c = ax.scatter(-data[:50,2] + np.pi, data[:50,1], c=data[:50,1], s=50, cmap='hsv', alpha=0.75)
plt.pause(0.05)

print("boop")
im_raw = car.get_picture()
print("doop")
image = im_raw
im_fig = ax2.imshow(image, animated=True)

def updatefig(*args):
    im_raw = car.get_picture()
    image = im_raw
    im_fig.set_array(image)
    return im_fig,

def updatelidar(*args):
    data = car.get_lidar()
    x = -data[:50,2] + np.pi*0.5
    y = data[:50,1]
    d = np.column_stack((x,y))
    c.set_offsets(d)
    c.set_color(cm.hsv(y/6000))
    return c,


ani = animation.FuncAnimation(fig, updatefig, interval=1, blit=True)
ani2 = animation.FuncAnimation(fig, updatelidar, interval=1, blit=True)

for update_nbr in range(1000):
    plt.pause(0.01)
