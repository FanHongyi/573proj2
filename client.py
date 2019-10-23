"""
NC STATE CSE 573 PROJECT 2

@author kylebeard, hongyifan

"""
import pickle
import socket
import struct
import sys
import threading
import time


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


def make_segments(fileName, MSS):
    global segments
    temp_segments = []
    with open(fileName, 'rb') as fp:
        while True:
            data = fp.read(MSS)
            if data:
                temp_segments.append(data)
            else:
                temp_segments.append(b'EOF')
                break
    sequenceNumber = 0
    indication = 0b0101010101010101
    for data in temp_segments:
        checkSum = calculate_checksum(data)
        # https://stackoverflow.com/questions/16926130/convert-to-binary-and-keep-leading-zeros-in-python
        # p = ['{0:032b}'.format(sequenceNumber), checkSum[2:], '{0:016b}'.format(indication), data]
        p = [format(sequenceNumber, '#034b'), format(int(checkSum, 2), '#018b'), bin(indication), data]
        # print(pickle.dumps(p))
        segments.append(pickle.dumps(p))
        sequenceNumber += 1


def threaded_function(sock, serversNotResponded):
    # if receive before expire, remove server from serversNotResponded
    ack, address = sock.recvfrom(4096)
    if verify_ack(ack, segment):
        serversNotResponded.remove(address[0])

# https://pymotw.com/3/socket/udp.html
def rdt_send(segment, servers):
    global portNum
    serversNotResponded = servers.copy()
    while serversNotResponded:
        # set a stopwatch
        now = time.time()
        future = now + 1
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for server in serversNotResponded:
            sock.sendto(segment, (server, portNum))
        while time.time() < future:
            # if receive before expire, remove server from serversNotResponded
            sock.settimeout(0.001)
            try:
                ack, address = sock.recvfrom(4096)
                if verify_ack(ack, segment):
                    serversNotResponded.remove(address[0])
            except socket.timeout:
                continue
            break
        sock.close()
        # Timeout, sequence number = Y
        if(serversNotResponded):
            print('Timeout, sequence number = ' + str(int(pickle.loads(segment)[0], base=2)))


def verify_ack(ack, segment):
    isValid = False
    if pickle.loads(ack)[0] == pickle.loads(segment)[0] and pickle.loads(ack)[1] == '0b0000000000000000' and pickle.loads(ack)[2] == '0b1010101010101010':
        print(str(int(pickle.loads(ack)[0], base=2)) + ' ack is valid')
        isValid = True
    # else:
    #     print(str(int(pickle.loads(ack)[0], base=2)) + ' ack is not valid')
    return isValid


# running client:
# python3 client.py server-1 server-2 server-3 server-port# file-name MSS
# python3 client.py '127.0.0.1' 7735 rfc8601.txt 3
if __name__ == "__main__":
    length = len(sys.argv)
    numServer = length - 4
    servers = sys.argv[1:numServer + 1]
    portNum = int(sys.argv[length - 3])
    fileName = sys.argv[length - 2]
    MSS = int(sys.argv[length - 1])

    # fileName = 'rfc8601.txt'
    # MSS = 3

    segments = []
    make_segments(fileName, MSS)

    for segment in segments:
        # print(pickle.loads(segment))
        # print(pickle.loads(segment)[0])
        # print('sequence number = ' + str(int(pickle.loads(segment)[0], base=2)))
        # print(segment)
        rdt_send(segment, servers)
        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # sock.sendto(segment, ('localhost', 10000))
        # ack, address = sock.recvfrom(4096)
        # print(pickle.loads(ack))
        # sock.close()