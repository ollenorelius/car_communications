"""Byte definitions for communication protocol."""
# Flags
START = 0x7E
END = 0x7E
ESC = 0x7D
ESC_XOR = 0x20


# Commands
CMD_STATUS = 0x01  # Status commands / requests
HEARTBEAT = 0x01
HANDSHAKE = 0x02
ASK_STATUS = 0x03
LATEST_CMD = 0x04

CMD_SET_PARAMS = 0x02
SET_MOT_THR = 0x01
DO_CALIB_GYRO = 0x02
ARM_MOTORS = 0x03
DISARM_MOTORS = 0x04

CMD_SPEED = 0x10  # Simple speed commands
WHEEL_SPD = 0x01  # int8 right, int8 left
CAR_SPD = 0x02  # int16 speed
TURN_SPD = 0x03  # int16 deg/s

CMD_SPEED_CL = 0x11  # Closed loop control
DIST_CL = 0x01  # int16 cm
TURN_CL = 0x02  # int16 deg
TURN_ABS_CL = 0x03  # int16 heading

REQ_SENS = 0x20  # Data requests
REQ_COMPASS = 0x01
REQ_ACC = 0x02
REQ_GYRO = 0x03
REQ_PIC = 0x04  # int8 cameraID
REQ_LIDAR = 0x05  # int8 lidarID

SENS = 0x30
SENS_LIDAR = 0x01  # int8 quality, int16 angle, int16 distance
SENS_ACC = 0x02  # int16 X, int16 Y, int16 Z
SENS_GYRO = 0x03  # int16 X, int16 Y, int16 Z
SENS_COMPASS = 0x04  # int16 heading
SENS_PIC = 0x06
SENS_SPEED = 0x05  # int16 speed, int16 turn
SENS_WHEEL = 0x07  # int16 FR, FL, RR, RL
SENS_TORQUE = 0x08  # int16 FR, FL, RR, RL
SENS_P_BATT = 0x09 # int16 mVolt, int16 mA
SENS_SONAR =  0x0A # int16 mm, int8 id

AUX_CMD = 0x40
HEADLIGHT_MODE = 0x01  # int8 mode


# Responses
R_OK = 0xA0
R_OK_IMAGE_FOLLOWS = 0x11

R_ERR = 0xB0  # general error
R_VAL_OOR = 0x21  # Out of range
R_FUNC_NA = 0x22  # Function not available
R_MAL_REQ = 0x23  # Malformed request

R_ST_INV = 0x30  # Vehicle state invalid
R_SENS_CAL = 0x31  # sensors calibrating
R_NO_HB = 0x32  # No heartbeat received
