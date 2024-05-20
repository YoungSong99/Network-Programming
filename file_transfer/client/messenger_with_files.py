import socket
import threading
import argparse
import os


class MessengerWithFiles:

    class Messenger(threading.Thread):
        def __init__(self, connection, is_server, l_port):
            threading.Thread.__init__(self)
            self.connection = connection
            self.is_server = is_server
            self.l_port = l_port

        def run(self):
            try:
                while True:
                    print("Enter an option ('m', 'f', 'x'):\n(M)essage (send)\n(F)ile (request)\ne(X)it ")
                    local_input = input()
                    if local_input == 'm':
                        print("Enter your message:")
                        message = input()
                        self.connection.sendall(message.encode('utf-8'))
                    elif local_input == 'f':
                        print("Which file do you want?")
                        file_name = input()
                        messenger = MessengerWithFiles()
                        receive_thread = messenger.FileTransfer(file_name, self.is_server, self.l_port)
                        receive_thread.start()
                    elif local_input == 'x':
                        self.connection.sendall(''.encode('utf-8'))
                        os._exit(0)
                    else:
                        print("Invalid option")

            except Exception as e:
                print(f"Error: {e}")
                os._exit(0)


    class FileTransfer(threading.Thread):
        def __init__(self, file_name, is_server, l_port):
            threading.Thread.__init__(self)
            self.file_name = file_name
            self.is_server = is_server
            self.l_port = l_port

        def run(self):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('localhost', self.l_port))
                    s.sendall(self.file_name.encode('utf-8'))
                    with open(self.file_name, 'wb') as file_out:
                        while True:
                            data = s.recv(1500)
                            if not data:
                                break
                            file_out.write(data)
            except Exception as e:
                print(f"Error: {e}")
                os._exit(0)

    class ClientConnection(threading.Thread):
        def __init__(self, l_port):
            threading.Thread.__init__(self)
            self.l_port = l_port

        def run(self):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                    server_socket.bind(('localhost', self.l_port))
                    server_socket.listen(1)
                    while True:
                        client_socket, _ = server_socket.accept()
                        with client_socket:
                            file_name = client_socket.recv(1500).decode('utf-8')
                            if os.path.exists(file_name):
                                with open(file_name, 'rb') as file_input:
                                    while True:
                                        file_buffer = file_input.read(1500)
                                        if not file_buffer:
                                            break
                                        client_socket.sendall(file_buffer)
            except Exception as e:
                print(f"Error: {e}")
                os._exit(0)

    class ServerConnection(threading.Thread):
        def __init__(self, server_socket):
            threading.Thread.__init__(self)
            self.server_socket = server_socket

        def run(self):
            try:
                while True:
                    client_socket, _ = self.server_socket.accept()
                    with client_socket:
                        file_name = client_socket.recv(1500).decode('utf-8')
                        if os.path.exists(file_name):
                            with open(file_name, 'rb') as file_input:
                                while True:
                                    file_buffer = file_input.read(1500)
                                    if not file_buffer:
                                        break
                                    client_socket.sendall(file_buffer)
            except Exception as e:
                print(f"Error: {e}")
                os._exit(0)

    @staticmethod
    def client(l_port, s_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(('localhost', s_port))
                client_socket.sendall(str(l_port).encode('utf-8'))
                messenger = MessengerWithFiles()
                connect_thread = messenger.ClientConnection(l_port)
                listen_thread = messenger.Messenger(client_socket, False, s_port)
                listen_thread.setDaemon(True)
                listen_thread.start()
                connect_thread.setDaemon(True)
                connect_thread.start()
                while True:
                    message = client_socket.recv(1500).decode('utf-8')
                    if not message:
                        break
                    print(message)
                client_socket.sendall(''.encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")

    @staticmethod
    def  server(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.bind(('localhost', port))
                server_socket.listen(1)
                client_socket, _ = server_socket.accept()
                with client_socket:
                    l_port = int(client_socket.recv(1500).decode('utf-8'))
                    messenger = MessengerWithFiles()
                    connect_thread = messenger.ServerConnection(server_socket)
                    listen_thread = messenger.Messenger(client_socket, True, l_port)
                    listen_thread.setDaemon(True)
                    listen_thread.start()
                    connect_thread.setDaemon(True)
                    connect_thread.start()
                    while True:
                        message = client_socket.recv(1500).decode('utf-8')
                        if not message:
                            break
                        print(message)
                    client_socket.sendall(''.encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Messenger with file transfer.')
    parser.add_argument('-l', type=int, required=True, help='Listening port number')
    parser.add_argument('-p', type=int, help='Port number of the server to connect to')
    parser.add_argument('-s', type=str, default='localhost', help='Address of the server to connect to')
    args = parser.parse_args()

    if args.p:
        MessengerWithFiles.client(args.l, args.p)
    else:
        MessengerWithFiles.server(args.l)
