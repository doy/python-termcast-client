import argparse
import hashlib
import json
import os
import shutil
import signal
import socket
import ssl
import sys

from . import pity
from . import py2compat

class Client(object):
    def __init__(self, host, port, username, password, tls, fingerprint):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls
        self.fingerprint = fingerprint

    def run(self, argv):
        self.sock = socket.socket()
        self.sock.connect((self.host, self.port))
        if self.tls:
            self._starttls()
        self.sock.send(self._build_connection_string())
        self.winch_set = False
        pity.spawn(
            argv,
            self._master_read,
            handle_window_size=True
        )

    def _starttls(self):
        self.sock.send(b'starttls\n')
        context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
        if self.fingerprint is not None:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        self.sock = context.wrap_socket(self.sock, server_hostname=self.host)
        if self.fingerprint is not None:
            remote = hashlib.sha1(self.sock.getpeercert(True)).hexdigest()
            if remote != self.fingerprint:
                raise Exception("Invalid fingerprint received: %s" % remote)

    def _master_read(self, fd):
        if not self.winch_set:
            self.prev_handler = signal.getsignal(signal.SIGWINCH)
            signal.signal(signal.SIGWINCH, self._winch)
            self.winch_set = True

        data = os.read(fd, 1024)
        self.sock.send(data)
        return data

    def _winch(self, signum, frame):
        self.prev_handler(signum, frame)
        # XXX a bit racy - should try to avoid splitting existing escape
        # sequences
        self.sock.send(self._build_winsize_metadata_string())

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
        if py2compat.py2:
            size = py2compat.get_terminal_size()
        else:
            size = shutil.get_terminal_size()
        return self._build_metadata_string({
            "geometry": [ size.columns, size.lines ],
        })

    def _build_metadata_string(self, data):
        return b'\033]499;' + json.dumps(data).encode('utf-8') + b'\007'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default="noway.ratry.ru")
    parser.add_argument('--port', type=int, default=31337)
    parser.add_argument('--username', default=os.getenv("USER"))
    parser.add_argument('--password', default="asdf")
    parser.add_argument('--tls', action='store_true')
    parser.add_argument('--fingerprint')
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
        tls=args.tls,
        fingerprint=args.fingerprint,
    )

    command = args.command
    if len(args.command) < 1:
        command = os.getenv("SHELL", default="/bin/sh")
    client.run(command)
