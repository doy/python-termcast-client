import os
import pty
import socket
import sys

class Client(object):
    def __init__(self):
        pass

    def run(self, argv):
        sock = socket.socket()
        sock.connect(("tozt.net", 2201))
        sock.send(b'hello doy asdf\n\033]499;{"geometry":[80,24]}\007')
        pty.spawn(argv, lambda fd: self._master_read(fd, sock))

    def _master_read(self, fd, sock):
        data = os.read(fd, 1024)
        sock.send(data)
        return data

if __name__ == '__main__':
    client = Client()
    # XXX options
    if len(sys.argv) > 1:
        client.run(sys.argv[1:])
    else:
        client.run(os.getenv("SHELL", default="/bin/sh"))
