# Author:   Toylerrr
# Date:     June 14, 2021
# Description:  Install printer definition and other scripts for the Elegoo Neptune 2.
# License:  GPLv3

import sys

from UM.Logger import Logger
try:
    from . import Installer 
    _installer = Installer.Installer()
    _registry = { "extension": _installer }
except ImportError:
    _registry = None
    Logger.log("w", "Could not import Neptune 2 profile")

def getMetaData():
    return {}

def register(app):
    if _registry is not None:
        _installer.installFiles(showMessage=False)
        return _registry
    return {}
