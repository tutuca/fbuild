import os
import sys
import glob
import component

def addOSComponents(env):
    # This is a base component, it will include the qt base include path
    modules = [
        'pthread',
    ]
    for module in modules:
        env.AddComponent(module, [], [], '', True)

