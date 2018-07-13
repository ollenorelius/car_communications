import zmq
import config_pb2 as config_proto
import time
if __name__ == '__main__':
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect ("tcp://localhost:5558")
    sub_socket.setsockopt(zmq.SUBSCRIBE, b'')
    proto_config = config_proto.Config()
    while True:
        msg = sub_socket.recv()
        protobuf_config = proto_config.ParseFromString(msg)
        print(proto_config)
        time.sleep(0.5)