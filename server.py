# -*- encoding: utf-8 -*-
# author: ldy
# date: 2021 4-9
import socket
import threading
import time
from datetime import datetime


class Server(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.__is_server_running = False
        self.__sock = None
        self.__curr_clients = {}
        # initializing for udp
        self._broadcasting_port = -1
        self._content = None
        self._interval_sec = 0

    def start(self, sock_type='tcp', **kwargs):
        if self.__is_server_running:
            print("You have started a server, and you can't start it againt!")
            return
        sock_type = sock_type.lower()
        if sock_type not in ['tcp', 'udp']:
            raise Exception('Invalid socket type.')
        if sock_type == 'udp':
            self._broadcasting_port = kwargs['broadcasting_port'] if 'broadcasting_port' in kwargs else None
            self._content = kwargs['broadcasted_content'] if 'broadcasted_content' in kwargs else None
            self._interval_sec = kwargs['interval_sec'] if 'interval_sec' in kwargs.keys(
            ) else None

        self.__is_server_running = True
        if 'mode' in kwargs:
            if kwargs['mode'] == 'threading':
                threading.Thread(target=Server.__listening if sock_type ==
                                 'tcp' else Server.__broadcasting, args=[self, ]).start()
        else:
            self.__listening(
                self) if sock_type == 'tcp' else self.__broadcasting(self)

    @staticmethod
    def __listening(self):
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        sock.settimeout(0.5)  # set accepting timeout
        sock.bind((self.host, self.port))
        sock.listen(5)  # maximum backlog is 5
        self.__sock = sock
        print(f'Current server is running at {self.host}:{self.port}')

        while self.__is_server_running:  # if the main work thread is closed, it won't be notified to other client.
            # accept a new client, create corresponding socket and put them into a new thread to deal with.
            try:
                # block here for 0.5s if have't any connecting request from the client
                client_sock, (remote_host, remote_port) = sock.accept()
            except socket.timeout:
                continue

            client_sock.settimeout(0.5)
            controller = _ThreadController(True)
            threading.Thread(target=Server.__recv, args=[
                client_sock, controller, remote_host, remote_port
            ]).start()
            pipe = []
            threading.Thread(target=Server.__send, args=[
                client_sock, controller, pipe
            ]).start()
            self.__curr_clients.update({
                f'{remote_host}:{remote_port}': {
                    'client_sock': client_sock,
                    'thread_controller': controller,
                    'pipe': pipe
                }
            })
            print(
                f'a new connection from {remote_host}:{remote_port} has connected!')

    @staticmethod
    def __broadcasting(self):
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,
                        1)  # set socket as broadcasting
        # get host by this computer name
        # bind this info to socket that could only receive message from corresponding port
        sock.bind((socket.gethostbyname(socket.gethostname()), self.port))
        self.__socket = sock

        # broadcasting settings
        broadcast_host = '255.255.255.255'
        broadcasted_content = self._content if self._content else 'hello everyone!'
        broadcasted_port = self._broadcasting_port if self._broadcasting_port else 9090
        interval_sec = self._interval_sec if self._interval_sec else 3

        print(f'Broadcasting...')

        while self.__is_server_running:
            # set broadcast port as 9090 and the process having port 9090 could receive the msg being broadcasted.
            sock.sendto(broadcasted_content.encode('utf-8'),
                        (broadcast_host, broadcasted_port))
            msg, (remote_host, remote_port) = sock.recvfrom(1024)
            msg = msg.decode('utf-8')
            print(
                f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  [{remote_host}:{remote_port}]: {msg}')
            time.sleep(interval_sec)

    def current_clients(self):
        return self.__curr_clients.keys()

    @property
    def state(self):
        return self.__is_server_running

    def stop(self):
        for client in self.current_clients():
            self.__curr_clients[client]['thread_controller'].state = False
            time.sleep(0.1)  # waiting for thread ending
            # release socket resource
            self.__curr_clients[client]['client_sock'].close()
        self.__is_server_running = False

    def send_to(self, host, port, msg):
        self.__curr_clients[f'{host}:{port}']['pipe'].append(msg)

    @staticmethod
    def __recv(sock, checker, remote_host, remote_port):
        while checker.state:
            buff = None  # clear buffer
            try:
                buff = sock.recv(1024).decode('utf-8')  # bin code to unicode
            except ConnectionResetError:
                pass
            except socket.timeout:
                continue
            if not buff or buff == 'exit':
                print(
                    f'the connection from {remote_host}:{remote_port} has been closed by remote client host')
                checker.state = False
                break
            print(
                f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  [{remote_host}:{remote_port}]: {buff}')

    @staticmethod
    def __send(sock, checker, pipe):
        while checker.state:
            if len(pipe) != 0:
                msg = pipe.pop()
                try:
                    sock.sendall(msg.encode('utf-8') if msg != '##' else '')
                except ConnectionResetError:
                    msg = '##'
                if msg == '##':
                    checker.state = False
                    break
                time.sleep(0.1)


# use this class to manage a work thread by itself
class _ThreadController(object):
    def __init__(self, stat=None):
        self.__stat = stat

    @property
    def state(self):
        return self.__stat

    @state.setter
    def state(self, val):
        self.__stat = val


if __name__ == '__main__':
    host_ip = socket.gethostbyname(socket.gethostname())
    s = Server('192.168.1.7', 65535)
    s.start()
