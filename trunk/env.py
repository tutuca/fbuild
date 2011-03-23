# FuDePan boilerplate requierd here

import os
import runpy
import shlex
import shutil
import sys

# this will need to be updated when updating scons version
SCONS_VERSION = "2.0.1"

# Some globals, dont worry, this is scripting :)
SCONS_DIR = os.path.join(os.getcwd(), "scons")
SCONS_VERSION_FILE = SCONS_VERSION.replace(".", "_")
SCONS_VERSION_FILE_PATH = os.path.join(SCONS_DIR, SCONS_VERSION_FILE)


def execfileWithArgs(filename, args=None):
    _globals = dict()
    _globals['__name__'] = '__main__'
    saved_argv = sys.argv
    sys.argv = list([filename])
    if isinstance(args, list):
        sys.argv.append(args)
    else:
        sys.argv.extend(shlex.split(args))
    exit_code = 0
    try:
        execfile(filename, _globals)
    except SystemExit as e:
        if isinstance(e.code, int):
            exit_code = e.code
        else:
            exit_code = 1
    except Exception:
        import traceback
        traceback.print_exc(file=sys.stderr)
        exit_code = 1
    finally:
        if args:
            sys.argv = saved_argv
    return exit_code


def askOk(prompt, retries=4, complaint='Yes or no, please!'):
    while True:
        ok = raw_input(prompt)
        if ok in ('y', 'ye', 'yes'):
            return True
        if ok in ('n', 'no', 'nop', 'nope'):
            return False
        retries = retries - 1
        if retries < 0:
            raise IOError('refusenik user')
        print complaint


def buildSCons():
    SCONS_SRC_DIR = SCONS_DIR + "-" + SCONS_VERSION
    if not os.path.exists(SCONS_SRC_DIR):
        sys.stderr.write("error: folder " + SCONS_SRC_DIR + " not found\n")
        sys.stderr.write("info: this folder is in fudepan-build repository\n")
        sys.exit(1)
    # python setup.py install --standalone-lib --prefix=$SCONS_TARGET_DIR
    try:
        shouldBuild = askOk("SCons is not built in your system, I have to do it, proceed?")
    except IOError as e:
        sys.stderr.write("error: user refusses to response\n")
        sys.stderr.write("hint: I cannot solve your problems this way\n")
        sys.exit(1)
    if shouldBuild:
        SCONS_BUILD_ARG = "install --standalone-lib --prefix=" + SCONS_DIR
        SCONS_BUILD_CMD = os.path.join(SCONS_SRC_DIR, "setup.py")
        execfileWithArgs(SCONS_BUILD_CMD, SCONS_BUILD_ARG)
        sconsVersionFile = open(SCONS_VERSION_FILE_PATH, "w")
        sconsVersionFile.close()
    else:
        sys.stderr.write("error: cannot continue without scons\n")
        sys.stderr.write("hint: next time say yes!\n")
        sys.exit(1)


if os.path.exists(SCONS_DIR):
    if not os.path.exists(SCONS_VERSION_FILE_PATH):
        # Need to update scons
        shutil.rmtree(SCONS_DIR)
        buildSCons()
else:
    # Need to build scons
    buildSCons()

SCONS_BIN_DIR = os.path.join(SCONS_DIR, "bin")
if not os.path.exists(SCONS_BIN_DIR):
    sys.stderr.write("error: scons folder corrupted, could not fin bin folder")
    sys.stderr.write("hint: remove scons folder and run again so it is regenerated")
    exit(1)

sys.stdout.write("Welcome to the FuDePan console environment\n")
