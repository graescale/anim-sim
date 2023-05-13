#*******************************************************************************
# content = imports as_launch.py.
#
# version      = 1.0.0
# date         = 2023-05-13
#
# author = Grae Revell <grae.revell@gmail.com>
#*******************************************************************************

import sys

LAUNCH_PATH = '/rodeo/dropbox/grevell/scripts'
if LAUNCH_PATH not in sys.path:
    sys.path.append(LAUNCH_PATH)

import as_launch
reload(as_launch)