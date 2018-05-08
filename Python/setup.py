from distutils.core import setup

setup(
    name='autonomous',
    version='1.0dev',
    packages=['autonomous', 'common', 'car_to_x/CarToCar'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.txt').read(),
)
