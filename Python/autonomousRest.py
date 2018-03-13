import threading
import time
from flask import Flask, send_file, make_response, request
import io
import json
import autonomous.car_controller

app = Flask(__name__)

car = autonomous.car_controller.CarController('autonomous-platform.local')
lock = threading.Lock()
buff = io.BytesIO()


@app.before_first_request
def activate_background_work():
    def run_job():
        while True:
            pic = car.get_picture(0)
            newImage = pic.resize((300, 200))
            newImage.save(buff, "jpeg", quality=40, optimize=True)
            with lock:
                buff.seek(0)
            time.sleep(0.005)

    thread = threading.Thread(target=run_job)
    thread.start()

@app.route("/")
def index():
    return "This is Root!"


@app.route('/image', methods=['GET'])
def get_image():
    with lock:
        data = buff.getvalue()
    fileSend = send_file(io.BytesIO(data), mimetype="image/jpeg", attachment_filename="pic.jpeg")
    return make_response(fileSend)


@app.route('/location', methods=['GET'])
def get_location():
    """todo get real car location"""
    lat = 57.704947
    lng = 11.963594

    location = [
        {'lat': lat, 'lng': lng}
    ]

    return json.dumps(location)


@app.route('/battery', methods=['GET'])
def get_battery():
    currentBattery = (car.get_voltage())
    return make_response(str(currentBattery))


@app.route('/speed', methods=['GET'])
def get_speed():
    wheel1 = car.get_wheel_speeds()[0] / 100
    wheel2 = car.get_wheel_speeds()[1] / 100
    wheel3 = car.get_wheel_speeds()[2] / 100
    wheel4 = car.get_wheel_speeds()[3] / 100
    allWheels = (wheel1 + wheel2 + wheel3 + wheel4) / 4
    speedDecimal = str(allWheels)
    speed = speedDecimal[:3]
    return make_response(speed)


@app.route('/odometer', methods=['GET'])
def get_odometer():
    return make_response("666")


@app.route('/steer', methods=['POST'])
def set_steering():
    print(request.form['turn'])
    print(request.form['speed'])
    turn = request.form['turn']
    speed = request.form['speed']
    car.set_turnrate(-int(float(turn)))
    car.set_speed(int(float(speed)))

    return make_response("ok")


@app.route('/lock', methods=['POST'])
def set_lock():
    lockStatus = request.form['lock']

    if lockStatus == "false":
        print(lockStatus)
        car.arm_motors()
    else:
        car.disarm_motors()
        print(lockStatus)
    return "ok"


@app.route('/lights', methods=['POST'])
def set_lights():
    lightsOn = request.form['lights']

    if lightsOn == "true":
        print(lightsOn)
        """car.arm_lights()"""
    else:
        print(lightsOn)
        """car.disarm_lights()"""
    return "ok"


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, port=5000)
