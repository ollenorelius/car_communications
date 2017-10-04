//Flags
#define START 0x7E
#define END 0x7E
#define ESC 0x7D
#define ESC_XOR 0x20


//Commands
#define CMD_STATUS 0x01 //Status commands / requests
#define HEARTBEAT 0x01
#define HANDSHAKE 0x02
#define ASK_STATUS 0x03

#define CMD_SET_PARAMS 0x02
#define SET_MOT_THR 0x01
#define DO_CALIB_GYRO 0x02


#define CMD_SPEED 0x10 //Simple speed commands
#define WHEEL_SPD 0x01
#define CAR_SPD 0x02
#define TURN_SPD 0x03


#define CMD_SPEED_CL 0x11 //Closed loop control
#define DIST_CL 0x01
#define TURN_CL 0x02
#define TURN_ABS_CL 0x03


#define REQ_SENS 0x20 //Data requests
#define REQ_COMPASS 0x01
#define REQ_ACC 0x02
#define REQ_GYRO 0x03


//Responses
#define R_OK 0x10

#define R_ERR 0x20 //general error
#define R_VAL_OOR 0x21 // Out of range
#define R_FUNC_NA 0x22 // Function not available
#define R_MAL_REQ 0x23 // Malformed request

#define R_ST_INV 0x30 // Vehicle state invalid
#define R_SENS_CAL 0x31 // sensors calibrating
#define R_NO_HB 0x32 // No heartbeat received
