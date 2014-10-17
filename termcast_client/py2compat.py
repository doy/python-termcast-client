import fcntl
import os
import struct
import sys
import termios

from collections import namedtuple

terminal_size = namedtuple('terminal_size', ['columns', 'lines'])

py2 = sys.version_info[0] == 2

def get_terminal_size(fallback=(80, 24)):
    """Based on Python 3 os.get_terminal_size()"""
    # columns, lines are the working values
    try:
        columns = int(os.environ['COLUMNS'])
    except (KeyError, ValueError):
        columns = 0

    try:
        lines = int(os.environ['LINES'])
    except (KeyError, ValueError):
        lines = 0

    # only query if necessary
    if columns <= 0 or lines <= 0:
        try:
            winsize = fcntl.ioctl(sys.__stdout__.fileno(),
                                  termios.TIOCGWINSZ, '\000' * 8)
            size = terminal_size(*struct.unpack('hhhh', winsize)[1::-1])

        except (NameError, OSError):
            size = terminal_size(*fallback)
        if columns <= 0:
            columns = size.columns
        if lines <= 0:
            lines = size.lines

    return terminal_size(*size)
