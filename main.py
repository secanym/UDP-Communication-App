import socket
import time
import zlib
import ntpath
from struct import *

def receiver():
    def listen(fragments):
        data_stream = []
        data_received = []
        for i in range(fragments):
            data_stream.append(b'')
            data_received.append(-1)

        while (-1 in data_received):
            received, client_adress = server_socket.recvfrom(1032)
            header = received[:8]
            data = received[8:]
            msg_type, num, crc = unpack('bhL', header)
            if crc == zlib.crc32(data):
                reply = pack('bhL', 7, num, 0)
                data_stream[num] = data
                data_received[num] = 1
                print("*Fragment", num, "received correctly*")
            else:
                reply = pack('bhL', 8, num, 0)
                print("*Fragment", num, "received incorrectly*")
            server_socket.sendto(reply, client_adress)

        final = b''
        for i in range(len(data_stream)):
            final = final + data_stream[i]

        return final

    server_port = int(input("Enter port number to listen on: "))

    server_ip = socket.gethostbyname(socket.gethostname())
    print("Your IP address is:",server_ip)

    spacer()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))

    data, client_adress = server_socket.recvfrom(1032)
    initiation = pack('bhL', 1, -1, 0)
    if data == initiation:
        server_socket.sendto(initiation, client_adress)
        print("Connection established")
        spacer()

    while(True):

        #Inicializacia komunikacie
        while (True):
            data, client_adress = server_socket.recvfrom(1032)
            msg_type, size, temp = unpack('bhL', data)
            if msg_type == 3 or msg_type == 4 or msg_type == 11:
                break

        if msg_type == 3:
            temp_data = listen(size)
            msg = temp_data.decode('utf-8')
            spacer()
            print("Received message:", msg)
            spacer()

        elif msg_type == 4:
            temp_data = listen(size)
            filename = temp_data.decode('utf-8')

            data, client_adress = server_socket.recvfrom(1032)
            msg_type, size, temp = unpack('bhL', data)

            filedata = listen(size)

            print("Path, where should be file",filename,"saved?")
            path = input()
            with open(path+"\\"+filename, "wb") as out_file:
                out_file.write(filedata)

            print("File was saved to:",path+"\\"+filename)
            spacer()

        elif msg_type == 11:
            termination = pack('bhL', 11, -1, 0)
            if data == termination:
               server_socket.sendto(termination, client_adress)
            break

def sender():
    def menu():
        print("Enter: 0 for terminating connection; 1 for sending text message; 2 for sending file")
        temp = int(input())
        spacer()
        return temp

    def initiate():
        c = 0
        client_socket.settimeout(0.5)
        while(c<5):
            c += 1
            try:
                data_send = pack('bhL', 1, -1, 0)
                client_socket.sendto(data_send, (server_ip, server_port))
                data_received, server_adress = client_socket.recvfrom(1032)
                if data_send == data_received:
                    print("Connection established")
                    spacer()
                    client_socket.settimeout(None)
                    return 0
            except:
                print("Connecting to receiver failed, trying again in",c,"seconds.")
                time.sleep(c)
        print("Failed to establish connection, ending")
        client_socket.settimeout(None)
        return -1

    def send_msg():
        msg = input("Enter message to send: ")
        msg = msg.encode('utf-8')

        print("Allow simulating faults during transmit? Enter: 1 for Yes; 2 for No")
        sim = int(input())

        send_data(msg, 5, sim)

    def send_file():
        path = input("Enter filepath for file:")
        filename = ntpath.basename(path)
        filename = filename.encode('utf-8')

        print("Allow simulating faults during transmit? Enter: 1 for Yes; 2 for No")
        sim = int(input())

        # Simulating faults explicitly turned off to avoid confusion with doubling fragment numbers
        send_data(filename, 6, 2)

        # Oosielanie suboru
        with open(path, "rb") as in_file:
            filedata = in_file.read()

        send_data(filedata, 6, sim)

    def end_conn():
        c = 0
        client_socket.settimeout(0.5)
        while (c < 5):
            c += 1
            try:
                data_send = pack('bhL', 11, -1, 0)
                client_socket.sendto(data_send, (server_ip, server_port))
                data_received, server_adress = client_socket.recvfrom(1032)
                if data_send == data_received:
                    print("Connection terminated")
                    spacer()
                    client_socket.settimeout(None)
                    return 0
            except:
                print("Failed to terminated connection, trying again in", c, "seconds")
                time.sleep(c)
        print("Failed to terminated connection, ending")
        print("----------------------------------------------------------------")
        client_socket.settimeout(None)
        return -1

    def send_data(data, msg_type, simulate_faults):
        data_stream = []
        data_confirmed = []

        if len(data) > max_size:
            for i in range(len(data)//max_size+1):
                data_stream.append(data[i*max_size:(i+1)*max_size])
                data_confirmed.append(-1)
        else:
            data_stream.append(data)
            data_confirmed.append(-1)

        # Initiation
        data_send = b''
        if msg_type == 5:
            data_send = pack('bhL', 3, len(data_stream), 0)
        if msg_type == 6:
            data_send = pack('bhL', 4, len(data_stream), 0)
        client_socket.sendto(data_send, (server_ip, server_port))

        client_socket.settimeout(0.2)
        while (-1 in data_confirmed):
            for i in range(len(data_stream)):
                if data_confirmed[i] == -1:
                    data_send = pack('bhL', msg_type, i, zlib.crc32(data_stream[i]))

                    x = ""
                    if simulate_faults == 1:
                        print("Simulate fault on fragment number", i, "? Enter 1 for Yes; Press Enter for No")
                        x = input()
                    if x == "":
                        client_socket.sendto(data_send + data_stream[i], (server_ip, server_port))
                    elif x == "1":
                        client_socket.sendto(data_send + data_stream[i][:len(data_stream[i]) // 2],
                                             (server_ip, server_port))

                    try:
                        data_received, server_adress = client_socket.recvfrom(1032)
                        msg_type, num, crc = unpack('bhL', data_received)
                        if msg_type == 7:
                            data_confirmed[num] = 1
                        if msg_type == 8:
                            data_confirmed[num] = -1
                    except:
                        print("Confirmation for fragment number", i, "not received")

        client_socket.settimeout(None)

    server_ip = input("Enter receiver's IP address: ")
    server_port = int(input("Enter receiver's port: "))

    while(True):
        max_size = int(input("Enter maximal fragment size (limited to 1024): "))
        if max_size <= 1024:
            break

    spacer()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if (initiate() == -1):
        return

    selector = menu()

    while (selector != 0):
        if selector == 1:
            send_msg()
        elif selector == 2:
            send_file()
        spacer()
        selector = menu()
    end_conn()

def spacer():
    print()
    print("----------------------------------------------------------------")
    print()


def main():
    while(True):
        print("(sender / receiver / end)")
        temp = input("Select mode: ")
        spacer()
        if temp == "sender":
            sender()
        elif temp == "receiver":
            receiver()
        elif temp == "end":
            return 0
        else:
            print("Entered mode not found. Try again!")

if __name__ == '__main__':
    main()