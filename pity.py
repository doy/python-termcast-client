import fcntl
import os
import pty
import signal
import termios
import tty

CHILD = pty.CHILD
STDIN_FILENO = pty.STDIN_FILENO
STDOUT_FILENO = pty.STDOUT_FILENO
STDERR_FILENO = pty.STDERR_FILENO

def fork(handle_window_size=False):
    # copied from pty.py, with modifications
    master_fd, slave_fd = openpty()
    slave_name = os.ttyname(slave_fd)
    pid = os.fork()
    if pid == CHILD:
        # Establish a new session.
        os.setsid()
        os.close(master_fd)

        if handle_window_size:
            clone_window_size_from(slave_name, STDIN_FILENO)

        # Slave becomes stdin/stdout/stderr of child.
        os.dup2(slave_fd, STDIN_FILENO)
        os.dup2(slave_fd, STDOUT_FILENO)
        os.dup2(slave_fd, STDERR_FILENO)
        if (slave_fd > STDERR_FILENO):
            os.close (slave_fd)

        # Explicitly open the tty to make it become a controlling tty.
        tmp_fd = os.open(os.ttyname(STDOUT_FILENO), os.O_RDWR)
        os.close(tmp_fd)
    else:
        os.close(slave_fd)

    # Parent and child process.
    return pid, master_fd, slave_name


def openpty():
    return pty.openpty()

def spawn(argv, master_read=pty._read, stdin_read=pty._read, handle_window_size=False):
    # copied from pty.py, with modifications
    # note that it references a few private functions - would be nice to not
    # do that, but you know
    if type(argv) == type(''):
        argv = (argv,)
    pid, master_fd, slave_name = fork(handle_window_size)
    if pid == CHILD:
        os.execlp(argv[0], *argv)
    try:
        mode = tty.tcgetattr(STDIN_FILENO)
        tty.setraw(STDIN_FILENO)
        restore = 1
    except tty.error:    # This is the same as termios.error
        restore = 0

    if handle_window_size:
        signal.signal(
            signal.SIGWINCH,
            lambda signum, frame: _winch(slave_name, pid)
        )

    while True:
        try:
            pty._copy(master_fd, master_read, stdin_read)
        except InterruptedError:
            continue
        except OSError:
            if restore:
                tty.tcsetattr(STDIN_FILENO, tty.TCSAFLUSH, mode)
        break

    os.close(master_fd)
    return os.waitpid(pid, 0)[1]

def clone_window_size_from(slave_name, from_fd):
    slave_fd = os.open(slave_name, os.O_RDWR)
    try:
        fcntl.ioctl(
            slave_fd,
            termios.TIOCSWINSZ,
            fcntl.ioctl(from_fd, termios.TIOCGWINSZ, " " * 1024)
        )
    finally:
        os.close(slave_fd)

def _winch(slave_name, child_pid):
    clone_window_size_from(slave_name, STDIN_FILENO)
    os.kill(child_pid, signal.SIGWINCH)
