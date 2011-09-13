# FuDePan boilerplate

import os
from termcolor import cprint

import subprocess

def runTest(target, source, env):
    app = str(source[0].abspath)
    if subprocess.call(app):
        cprint('TEST ERROR: %s' % app, 'red')
    else:
        cprint('TEST OK: %s' % app, 'green')

def configure(target, source, env):
    makefile = str(target[0].abspath)
    buildDir = os.path.split(makefile)[0]

    configure = str(source[0].abspath)
    configureOpts = (' --bindir=%(INSTALL_BIN_DIR)s --libdir=%(INSTALL_LIB_DIR)s --includedir=%(INSTALL_HEADERS_DIR)s' % env)
    p = subprocess.Popen(configure + configureOpts, cwd=buildDir, shell=True)
    if p.wait() != 0:
        return p.wait()

    p = subprocess.Popen('make', cwd=buildDir, shell=True)
    if p.wait() != 0:
        return p.wait()

    p = subprocess.Popen('make install', cwd=buildDir, shell=True)
    return p.wait()

