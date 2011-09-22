# FuDePan boilerplate

import os
import platform
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
    if not os.path.exists(buildDir):
        os.makedirs(buildDir)

    configure = env['configurePath']
    configureOpts = (' --bindir=%(INSTALL_BIN_DIR)s --libdir=%(INSTALL_LIB_DIR)s --includedir=%(INSTALL_HEADERS_DIR)s' % env)

    procEnv = os.environ
    (arch,binType) = platform.architecture()
    if arch == '64bit':
        procEnv["CXXFLAGS"] = str(env["CXXFLAGS"])
        procEnv["CFLAGS"] = '-fPIC'

    p = subprocess.Popen(configure + configureOpts, cwd=buildDir, shell=True, env=procEnv)
    if p.wait() != 0:
        return p.wait()

    p = subprocess.Popen('make', cwd=buildDir, shell=True, env=procEnv)
    if p.wait() != 0:
        return p.wait()

    p = subprocess.Popen('make install', cwd=buildDir, shell=True, env=procEnv)
    return p.wait()

