import os
import sys
import glob

def addBoostComponents(env):
    # This is a base component, it will include the qt base include path
    validModules = [
	'boost_system',
        'boost_thread'
        ]
    for module in validModules:
        env.AddComponent(module, [], [], '', True)

