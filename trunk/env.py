# FuDePan boilerplate requierd here

import os
import sys

BUILD_SCRIPTS_DIR = os.path.join(os.getcwd(), "buildscripts")
sys.path.append(BUILD_SCRIPTS_DIR)

from termcolor import cprint
cprint('Welcome to the FuDePan console environment','green', None, ['bold'])

