import sys


def log(*args, **kwargs):
    sys.stderr.write(*args, **kwargs)
    sys.stderr.write('\n')
