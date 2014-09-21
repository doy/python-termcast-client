import argparse
import os
import pty
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
        sock.send(self._build_connection_string().encode('utf-8'))
        pty.spawn(argv, lambda fd: self._master_read(fd, sock))

    def _master_read(self, fd, sock):
        data = os.read(fd, 1024)
        sock.send(data)
        return data

    def _build_connection_string(self):
        auth = "hello %s %s\n" % (self.username, self.password)
        metadata = '\033]499;{"geometry":[80,24]}\007' # XXX
        return auth + metadata

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
