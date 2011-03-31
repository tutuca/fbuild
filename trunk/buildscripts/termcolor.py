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

