""" Implemented for testing the BLE buttons

This module is a simple test case for BLE buttons like the Logitech (c) POP.
It's only used for debugging purposes.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from threading import Event
from time import sleep
import logging
import sys
from .ble_interaction import WhiteboardBotBLE
from .feedbacker import Message, send_feedback
from . import read_config as wbconf

# 60s * 60m * 24h * 30d = 2592000
THIRTY_DAYS_IN_SECONDS = 2592000


def main():
    """ Main function to start all processes """
    logging.basicConfig(filename=wbconf.get_key("Other", "error_log"),
                        format='%(asctime)s %(message)s', level=logging.DEBUG)
    logger = logging.getLogger()
    ble_trigger = Event()
    trigger_button = {}
    ble_thread = None
    button_list = []
    for i in range(int(wbconf.get_key('Output', 'num_buttons'))):
        button_list.append(dict(wbconf.get_section('Button' + str(i))))
    try:
        ble_thread = WhiteboardBotBLE(ble_trigger, trigger_button, button_list)
        ble_thread.start()
    except: # pylint: disable=bare-except
        logger.exception('BLE init failed')

    while True:
        try:
            while not ble_thread.isAlive():
                # Restard BLE
                ble_thread.start()
                sleep(5)

            ble_trigger.wait()

            #ble_thread.scanner.stop()
            ble_thread.scanner.clear()
            send_feedback(Message.TRIGGER)

            # Done
            ble_trigger.clear()
        except: # pylint: disable=bare-except
            logger.exception('Error in Main loop')
            sys.exit()

if __name__ == '__main__':
    main()
