"""Manages all interactions with BLE

This module handles all interactions with BLE, specifically with the Logitech (c) POP.
It should work with ANY product, that sends a BLE signal.
It build to be a separate thread, so we can use it as a trigger in an application.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from threading import Thread
# bluepy isn't really maintained anymore, but the alternatives have bad documentation and this works
import time
from random import random
import bluepy.btle


# NOTE: Also "normal" Bluetooth? -> Bluepy only checks BLE right now


class WhiteboardBotBLE(Thread):
    """Init triggers, get known buttons, start scanner."""

    def __init__(self, trigger, button, button_list):
        """Init triggers,  buttons and scanner"""

        self.trigger = trigger
        self.button = button
        Thread.__init__(self)
        # We want this to run as a daemon, because that's exactly what this is
        Thread.daemon = True
        self.delegate = ScanDelegate(trigger, button_list, button)
        self.scanner = bluepy.btle.Scanner().withDelegate(self.delegate)

    def run(self):
        """Run the scanner loop."""
        while True:
            try:
                # Let it scan for a second, which is much more stable than
                # microseconds but still snappy
                self.scanner.scan(1)
            except bluepy.btle.BTLEManagementError:
                time.sleep(random())


# Class is overriding ScanDelegate
# pylint: disable=too-few-public-methods
class ScanDelegate(bluepy.btle.DefaultDelegate):
    """Init and set triggers on discovery of device from MAC-address."""
    button_list = None

    def __init__(self, trigger, button_list, button):
        """Init triggers and buttons."""
        bluepy.btle.DefaultDelegate.__init__(self)
        bluepy.btle.DefaultDelegate.discovered = False
        self.trigger = trigger
        ScanDelegate.button_list = button_list
        self.button = button

    # Method is overriding handleDiscovery from ScanDelegate
    # pylint: disable=unused-argument, invalid-name
    def handleDiscovery(self, dev, isNewDev, isNewData):
        """Override handleDiscovery to only look for our MAC-addresses. Set trigger, save button."""
        if isNewDev:
            # Loops through whole list of buttons
            for i in range(len(ScanDelegate.button_list)):
                # If the mac address is in this list
                if dev.addr in ScanDelegate.button_list[i]['mac']:
                    # Button was correctly detected, trigger whiteboard
                    self.trigger.set()
                    # Save information about, which button was triggered
                    self.button.update(ScanDelegate.button_list[i])
                    bluepy.btle.DefaultDelegate.discovered = False
