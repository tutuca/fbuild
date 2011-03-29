# FuDePan boilerplate required here

import fnmatch
import os

def WalkDirsForSConscript(env, topdir):
    for root, dirnames, filenames in os.walk(topdir):
        for filename in fnmatch.filter(filenames, 'SConscript'):
            (headPath,tailPath)=os.path.split(root)
            variantPath = os.path.join(env['BUILD_DIR'], tailPath)
            env.SConscript(os.path.join(root, filename), variant_dir=variantPath, duplicate=0, exports='env')
