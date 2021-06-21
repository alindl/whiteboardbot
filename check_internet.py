"""
Simple internet connection check

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

import os

def internet():
    """
    Check internet through pulling a txt file. This is how NetworkManager in Arch Linux does it.
    It also makes sure, that the whiteboardbot has a real internet connection,
    not just a web portal.

    Host: http://ping.archlinux.org

    """

    try:
        result = os.popen("curl -s http://ping.archlinux.org/nm-check.txt").read()
        if result == "NetworkManager is online\n":
            return True
        return False
    except OSError:
        return False


internet()
