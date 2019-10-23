"""
NC STATE CSE 573 PROJECT 2

@author kylebeard, hongyifan

------------------------------
The server listens on the well-known port 7735. It implements the receiver side of the Stop-and-Wait protocol,
as described in the book. Specifically, when it receives a data packet, it computes the checksum and checks
whether it is in-sequence, and if so, it sends an ACK segment (using UDP) to the client; it then writes
the received data into a file whose name is provided in the command line. If the packet received is out-ofsequence,
an ACK for the last received in-sequence packet is sent;, if the checksum is incorrect, the receiver does nothing.

"""

import pickle
import socket
import sys
from random import random


def calculate_checksum(data):
    pos = len(data)
    if pos & 1:
        pos -= 1
        res = data[pos]
    else:
        res = 0
    while pos > 0:
        pos -= 2
        res += (data[pos + 1]) << 8 + data[pos]
    res = (res >> 16) + (res & 0xffff)
    res += (res >> 16)

    result = (~res) & 0xffff
    result = result >> 8 | ((result & 0xff) << 8)
    return bin(result)


def verify_checksum(checksum, message):
    pos = len(message)
    if pos & 1:
        pos -= 1
        res = message[pos]
    else:
        res = 0
    while pos > 0:
        pos -= 2
        res += (message[pos + 1]) << 8 + message[pos]
    res = (res >> 16) + (res & 0xffff)
    res += (res >> 16)

    result = (~res) & 0xffff
    result = result >> 8 | ((result & 0xff) << 8)
    # print(int(checksum, 2), result)
    # print(bin(result))
    if result == int(checksum, 2):
        return True
    else:
        return False


# running server:
# python3 server.py port# file-name p
# python3 server.py 7735 res.txt 0.5
if __name__ == "__main__":
    portNum = int(sys.argv[1])
    fileName = sys.argv[2]
    probability = float(sys.argv[3])
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind the socket to the port
    server_address = ('localhost', portNum)
    sock.bind(server_address)

    while True:
        data, address = sock.recvfrom(4096)
        r = random()
        segment = pickle.loads(data)
        if r > probability:
            if verify_checksum(segment[1], segment[3]):
                # TODO: check if segment is in sequence
                ack = [segment[0], format(0, '#018b'), bin(0b1010101010101010)]
                sent = sock.sendto(pickle.dumps(ack), address)
                # TODO: it then writes the received data into a file whose name is provided in the command line
        else:
            print('Packet loss, sequence number = ' + str(int(segment[0], 2)))
