# FuDePan boilerplate requierd here

import sys

from sys import stdout

def error(string, is_tty=stdout.isatty()):
    return ('\033[31;1m' + string + '\033[0m') if is_tty else string

def standout(string, is_tty=stdout.isatty()):
    return ('\033[34;1m' + string + '\033[0m') if is_tty else string

def msg(string, is_tty=stdout.isatty()):
    return ('\033[1;32m' + string + '\033[1;m') if is_tty else string

print msg('Welcome to the FuDePan console environment')

