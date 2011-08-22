# FuDePan boilerplate requierd here

import os
import sys

BUILD_SCRIPTS_DIR = os.path.join(os.getcwd(), "site_scons")
sys.path.append(BUILD_SCRIPTS_DIR)

# Get the QT Directory
QTDIR = os.environ.get('QTDIR',None)
if not QTDIR:
    os.putenv('QTDIR','/usr')

# Welcome message    
from termcolor import cprint
cprint('Welcome to the FuDePan console environment','green')
