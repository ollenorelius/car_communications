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

CMD_SET_PARAMS = 0x02
SET_MOT_THR = 0x01
DO_CALIB_GYRO = 0x02


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


# Responses
R_OK = 0x10
R_OK_IMAGE_FOLLOWS = 0x11

R_ERR = 0x20  # general error
R_VAL_OOR = 0x21  # Out of range
R_FUNC_NA = 0x22  # Function not available
R_MAL_REQ = 0x23  # Malformed request

R_ST_INV = 0x30  # Vehicle state invalid
R_SENS_CAL = 0x31  # sensors calibrating
R_NO_HB = 0x32  # No heartbeat received
