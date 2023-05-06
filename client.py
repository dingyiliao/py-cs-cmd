# -*- encoding: utf-8 -*-
import socket
import threading
import time
from datetime import datetime


class Client(object):
    def __init__(self, host, port, pipe):
        self.remote_host = host
        self.remote_port = port
        self.curr_host = None
        self.curr_port = None
        self.pipe = pipe
        self._stat = False
        self._recv_stat, self._send_stat = False, False
        self._socket = None
        self._curr_host = None
        self._curr_port = -1

    @staticmethod
    def __recv(self):
        while self._recv_stat:
            try:
                msg = self._socket.recv(1024).decode()
            except ConnectionResetError:
                msg = 'exit'
            except socket.timeout:
                continue
            if msg == '' or msg == 'exit':  # remote host has been closed
                self.__show_message(
                    'remote host has been closed the connection to us')
                self.stop()
                break
            self.__show_message(msg, msg_type='recv_msg',
                                sock=self.__socket.getpeername())

    @staticmethod
    def __send(self):
        while self.__send_stat:
            if len(self.pipe) != 0:
                msg = self.pipe.pop()
                self.__socket.sendall(msg.encode('utf-8'))
                if msg == 'exit':
                    self.stop()
                    break
                time.sleep(0.1)

    def __show_message(self, string, msg_type='sys_notf', sock=None):
        if msg_type.lower() not in ['recv_msg', 'sys_notf']:
            prefix = ''
        elif msg_type == 'recv_msg':
            assert sock is not None and isinstance(sock, tuple)
            host, port = sock
            prefix = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][{host}:{port}] : "
        else:
            prefix = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][{self._curr_host}:{self._curr_port}] : "
        print(prefix + string)

    @property
    def state(self):
        return self._stat

    def start(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(0.5)
        self._socket.connect((self.remote_host, self.remote_port))

        self._curr_host, self._curr_port = self._socket.getsockname()
        self.__show_message(
            f'Connected to {self.remote_host}:{self.remote_port}!')
        self._recv_stat = True
        self._send_stat = True
        self._stat = True
        threading.Thread(target=self.__recv, args=[self]).start()
        threading.Thread(target=self.__send, args=[self]).start()

    def stop(self):
        self._recv_stat = False
        self._send_stat = False
        self._stat = False

    def __repr__(self):
        return f'[{self._curr_host}:{self._curr_port}]'

    def __str__(self):
        return self.__repr__()


if __name__ == '__main__':
    pip = []
    # client = Client(socket.gethostbyname(socket.gethostname()), 443, pipe)
    client = Client('192.168.1.7', 65535, pip)
    client.start()

    while client.state:
        msg = input()
        pip.append(msg)
