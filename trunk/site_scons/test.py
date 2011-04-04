# FuDePan boilerplate

import os
from termcolor import cprint

def runTest(target, source, env):
    app = str(source[0].abspath)
    if os.spawnl(os.P_WAIT, app, app)!=0:
        cprint('TEST ERROR: %s' % app, 'red')
    else:
        cprint('TEST OK: %s' % app, 'green')

