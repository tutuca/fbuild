# http://www.scons.org/wiki/ColorBuildMessages
import sys
import os

colors = {}
colors['cyan']   = '\033[96m'
colors['purple'] = '\033[95m'
colors['blue']   = '\033[94m'
colors['green']  = '\033[92m'
colors['yellow'] = '\033[93m'
colors['red']    = '\033[91m'
colors['end']    = '\033[0m'

#If the output is not a terminal, remove the colors
if not sys.stdout.isatty():
   for key, value in colors.iteritems():
      colors[key] = ''

compile_source_message = '%s[compiling] $SOURCE%s' % (colors['blue'], colors['end'])
link_program_message = '%s[linking program] $TARGET%s' % (colors['cyan'], colors['end'])
link_library_message = '%s[linking static] $TARGET%s' % (colors['cyan'], colors['end'])
link_shared_library_message = '%s[linking shared] $TARGET%s' % (colors['cyan'], colors['end'])
ranlib_library_message = '%s[indexing] $TARGET%s' % (colors['purple'], colors['end'])
install_message = '%s[installing] $SOURCE => $TARGET%s' % (colors['green'], colors['end'])
qtuic_message = '%s[uic] $SOURCE%s' % (colors['blue'], colors['end'])
qtmoc_message = '%s[moc] $SOURCE%s' % (colors['blue'], colors['end'])

def cprint(msg,color):
    print('%s%s%s' % (colors[color], msg, colors['end']))
    
def prettyMessages(env):
    env['CCCOMSTR'] = compile_source_message
    env['CXXCOMSTR'] = compile_source_message
    env['SHCCCOMSTR'] = compile_source_message
    env['SHCXXCOMSTR'] = compile_source_message
    env['ARCOMSTR'] = link_library_message
    env['RANLIBCOMSTR'] = ranlib_library_message
    env['SHLINKCOMSTR'] = link_shared_library_message
    env['LINKCOMSTR'] = link_program_message
    env['INSTALLSTR'] =  install_message
    env['QT_UICCOMSTR'] = qtuic_message
    #env['QT_RCCCOMSTR'] = rcc
    env['QT_MOCFROMHCOMSTR'] = qtmoc_message
    env['QT_MOCFROMCXXCOMSTR'] = qtmoc_message
    #env['QT_LUPDATECOMSTR'] = ts
    #env['QT_LRELEASECOMSTR'] = qm
