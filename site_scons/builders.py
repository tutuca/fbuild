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
    buildDir = env['buildDir']
    configure = env['configurePath']
    configureOpts = (' --bindir=%(INSTALL_BIN_DIR)s --libdir=%(INSTALL_LIB_DIR)s --includedir=%(INSTALL_HEADERS_DIR)s' % env)
    procEnv = os.environ
    (arch,binType) = platform.architecture()
    if arch == '64bit':
        procEnv["CXXFLAGS"] = str(env["CXXFLAGS"])
        procEnv["CFLAGS"] = '-fPIC'

    return subprocess.call(configure + configureOpts + ' ; make; make install', cwd=buildDir, shell=True, env=procEnv)

