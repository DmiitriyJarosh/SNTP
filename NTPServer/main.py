import socket
import sys
import time
from queue import Queue, Empty
from threading import Thread
from select import select

from packet import Packet, ZERO_TIME_DELTA

tasks_queue = Queue()
is_stopped = False


class Receiver(Thread):
    def __init__(self, socket):
        Thread.__init__(self)
        self.socket = socket

    def run(self):
        while True:
            if is_stopped:
                break

            read_packets, _, _ = select([self.socket], [], [], 1)
            if len(read_packets) > 0:
                print("Received {} packets".format(len(read_packets)))
                for socket in read_packets:
                    packet, address = socket.recvfrom(1024)
                    received_time = time.time() + ZERO_TIME_DELTA
                    tasks_queue.put((packet, address, received_time))


class Worker(Thread):
    def __init__(self, socket):
        Thread.__init__(self)
        self.socket = socket

    def run(self):
        while True:
            if is_stopped:
                break

            try:
                data, addr, received_time = tasks_queue.get(timeout=1)
                received_packet = Packet(data=data)
                answer_packet = Packet(version=3, mode=4)

                # we think that we take from first level server
                answer_packet.stratum = 2
                answer_packet.poll = 10

                # emulate that we have taken time before receiving
                answer_packet.reference_time = received_time - 3

                # copy time to originate field
                answer_packet.originate_time_high = received_packet.transmit_time_high
                answer_packet.originate_time_low = received_packet.transmit_time_low

                # fill receive and transmit times
                answer_packet.received_time = received_time
                answer_packet.transmit_time = time.time() + ZERO_TIME_DELTA

                # send packet to client
                socket.sendto(answer_packet.bytes(), addr)
                print("Answered to {0}:{1}".format(addr[0], addr[1]))
            except Empty:
                continue


# Usage: main.py ip port
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: main.py ip port")
        exit(-1)

    ip = sys.argv[1]
    port = int(sys.argv[2])

    socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket.bind((ip, port))
    print("Server will start on: ", socket.getsockname())

    receiver = Receiver(socket)
    worker = Worker(socket)

    receiver.start()
    worker.start()

    while True:
        time.sleep(1)
