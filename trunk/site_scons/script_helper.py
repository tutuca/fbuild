import sys

options = ' '.join([arg for arg in sys.argv if arg.startswith('-')])
args = ','.join([arg for arg in sys.argv[1:] if not arg.startswith('-')])

cmd = "/usr/bin/scons " + options

if args:
    cmd += ' targets=%s' % args
print cmd
