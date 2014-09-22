import argparse
import json
import os
import pity
import shutil
import signal
import socket
import sys

class Client(object):
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def run(self, argv):
        sock = socket.socket()
        sock.connect((self.host, self.port))
        sock.send(self._build_connection_string())
        self.winch_set = False
        pity.spawn(
            argv,
            lambda fd: self._master_read(fd, sock),
            handle_window_size=True
        )

    def _master_read(self, fd, sock):
        if not self.winch_set:
            prev_handler = signal.getsignal(signal.SIGWINCH)
            signal.signal(
                signal.SIGWINCH,
                lambda signum, frame: self._winch(
                    sock,
                    lambda: prev_handler(signum, frame)
                )
            )
            self.winch_set = True

        data = os.read(fd, 1024)
        sock.send(data)
        return data

    def _winch(self, sock, prev_handler):
        prev_handler()
        # XXX a bit racy - should try to avoid splitting existing escape
        # sequences
        sock.send(self._build_winsize_metadata_string())

    def _build_connection_string(self):
        auth = (
            b'hello ' +
            self.username.encode('utf-8') +
            b' ' +
            self.password.encode('utf-8') +
            b'\n'
        )
        metadata = self._build_connection_metadata_string()
        return auth + metadata

    def _build_connection_metadata_string(self):
        # for now
        return self._build_winsize_metadata_string()

    def _build_winsize_metadata_string(self):
        size = shutil.get_terminal_size()
        return self._build_metadata_string({
            "geometry": [ size.columns, size.lines ],
        })

    def _build_metadata_string(self, data):
        return b'\033]499;' + json.dumps(data).encode('utf-8') + b'\007'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="noway.ratry.ru")
    parser.add_argument('--port', type=int, default=31337)
    parser.add_argument('--username', default=os.getenv("USER"))
    parser.add_argument('--password', default="asdf")
    parser.add_argument(
        'command',
        nargs=argparse.REMAINDER,
    )

    args = parser.parse_args(sys.argv[1:])

    client = Client(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
    )

    command = args.command
    if len(args.command) < 1:
        command = os.getenv("SHELL", default="/bin/sh")
    client.run(command)
