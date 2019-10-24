"""
NC STATE CSE 573 PROJECT 2

@author kylebeard, hongyifan

"""

import pickle
import socket
import sys
from random import random

# this function verifies the received checksum in the segment with the message body
def verify_checksum(checksum, message):

    # get the byte length
    pos = len(message)

    # convert message to binary checksum
    if pos & 1:
        pos -= 1
        res = message[pos]
    else:
        res = 0
    while pos > 0:
        pos -= 2
        res += (message[pos + 1]) << 8 + message[pos]

    # binary addition
    res = (res >> 16) + (res & 0xffff)
    res += (res >> 16)
    result = (~res) & 0xffff
    result = result >> 8 | ((result & 0xff) << 8)

    # check if result matches checksum integer
    if result == int(checksum, 2):
        return True
    else:
        return False


# running server:
# (format) python3 server.py port# file-name p
# (copy me) python3 server.py 7735 result.txt 0.25
if __name__ == "__main__":

    # get parameters from command line
    portNum = int(sys.argv[1])
    fileName = sys.argv[2]
    probability = float(sys.argv[3])

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the port
    server_address = ('', portNum)
    sock.bind(server_address)

    print("server started and listening...")

    # initialize sequence number
    expectedSequence = 0

    # initialize previous ackpacket to seq = 0
    prevAck = ['{0:08b}'.format(0), format(0, '#018b'), bin(0b1010101010101010)]

    while True:

        print("---")

        # fetch data from the UDP socket
        data, address = sock.recvfrom(4096)

        # create segment and extract byte message
        segment = pickle.loads(data)
        message = segment[3].decode("utf-8")
        print("received message: " + message)

        # convert received sequence from binary to int
        recvSequence = int(segment[0], 2)

        # generate random decimal (0.0 to 1.0)
        r = random()

        # simulate packet loss if random number above parameter input given
        if r > probability:

            if verify_checksum(segment[1], segment[3]):

                print("checksum verified")

                #print("sequence expected " + str(expectedSequence))
                #print("sequence received " + str(recvSequence))

                # create ack for current segment
                ack = [segment[0], format(0, '#018b'), bin(0b1010101010101010)]
                print((expectedSequence, recvSequence))

                # check if sequence is out of order
                if expectedSequence != recvSequence:
                    print("sequence out of order, resending previous ack")
                    # send chosen ack based on sequence in order
                    sent = sock.sendto(pickle.dumps(prevAck), address)
                else:
                    print("sequence verified")
                    # send chosen ack based on sequence in order
                    sent = sock.sendto(pickle.dumps(ack), address)
                    # write data to output file specific from p2mpserver invokation
                    if message == "EOF":
                        print("end of file transfer")
                    else:
                        print("writing file")
                        f = open(fileName, "a+")
                        f.write(message)
                        f.close()
                    # increment for next iteration
                    expectedSequence += 1
                    prevAck = ack
            else:
                print("checksum not verified")
        else:
            print('Packet loss, sequence number = ' + str(int(segment[0], 2)))