"""
Main file of the whiteboardbot, orchestrating the communication between the parts

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from threading import Event
from time import sleep, time
import logging
import sys
# TODO Must add "from ." to either of those imports
from .ble_interaction import WhiteboardBotBLE
from .feedbacker import Message, send_feedback, reset_feedback
from . import image_processor as wbpic
from . import read_config as wbconf
from . import uploader as wbup
from . import check_internet as wbci
from .slack_processor import SlackBot

# 60s * 60m * 24h * 30d = 2592000
THIRTY_DAYS_IN_SECONDS = 2592000

def main():
    """ Main function to start all processes """
    logging.basicConfig(filename=wbconf.get_key("Other", "error_log"),
                        format='%(asctime)s %(message)s', level=logging.DEBUG)
    logger = logging.getLogger()
    # Used to trigger execution after button was pressed
    ble_trigger = Event()
    # Used to save specific button information and corresponding targets that are mapped to that button
    trigger_button, upload_targets = {}, {}
    all_upload_targets = wbup.get_upload_targets()
    ble_thread = None
    remove = True
    post_later, button_list = [], []
    # slack_bot = None
    # if bool(int(wbconf.get_key('Output', 'slack'))):
    #     slack_bot = SlackBot()
    for i in range(int(wbconf.get_key('Output', 'num_buttons'))):
        button_list.append(dict(wbconf.get_section('Button' + str(i))))
    try:
        ble_thread = WhiteboardBotBLE(ble_trigger,
                                      trigger_button,
                                      [dict(wbconf.get_section('Button' + str(i)))
                                       for i in range(int(wbconf.get_key('Output', 'num_buttons')))])
        ble_thread.start()
    except RuntimeError:
        # Maybe there are other errors to catch here
        logger.exception('BLE init failed')

    try:
        while not ble_thread.isAlive():
            ble_thread.start()
            print("restart ble")
            sleep(5)

        ble_trigger.wait()

        # ble_thread.scanner.stop()
        ble_thread.scanner.clear()
        send_feedback(Message.TRIGGER)

        print("Taking picture")
        # pictures = []
        pictures, file_name = wbpic.make_pic()
        # The appended and not enhanced picture is at the end
        # Enhanced picture (if requested) next to last

        enhancer, enhanced_file = None, None
        if wbconf.get_bool_key('Output', 'enhance'):
            print('enhancing')

            enhancer, enhanced_file = wbpic.enhance(file_name)
            print("enhanced")

        print('PNG to JPG')

        final_file = wbpic.convert_png_to_jpg(file_name)
        pictures.append(final_file)
        if wbconf.get_bool_key('Output', 'enhance'):
            pictures.append(enhanced_file)

        print('Upload')
        print(pictures)

        reminder_ts = 0
        # Get targets for button, upload to those
        if wbci.internet():
            print('On the interwebs')
            if not remove:
                reminder_ts = wbup.send_reminders(all_upload_targets)
                # Practically clear targets
                # all_upload_targets = wbup.get_upload_targets()
                _ = wbup.get_upload_targets()
            wbup.upload(trigger_button, pictures, enhancer,
                        SlackBot() if wbconf.get_bool_key('Output', 'slack') else None)
            remove = True
            # This is not going to remove older unsent pictures
        else:
            send_feedback(Message.ERROR)
            upload_targets = wbup.set_upload_targets(trigger_button['action'].split(','))
            # all_upload_targets = wbup.save_all_targets(all_upload_targets, upload_targets)
            _ = wbup.save_all_targets(all_upload_targets, upload_targets)
            remove = False

        print("before remove: ")
        if remove:
            print("remove I guess")
            if len(post_later) > 0 and ((time() - reminder_ts) > THIRTY_DAYS_IN_SECONDS):
                pass
                # TODO Should we even bother?
                # Currently we don't save state between button presses
                # Yeah, it there's another outage and trigger within 30 days
                # they are going to be kept longer. It's not a bug, it's a feature!
                # pictures.append(post_later)
                # post_later = []
            print("removing: " + str(pictures))

            wbpic.remove_pictures(pictures)

        else:
            print("didn't remove: No internet connection. Remind later.")
            post_later.append(pictures.copy())
        ble_trigger.clear()
    except:  # Yeah, this is just for debugging
        logger.exception('Error in Main loop')
        sys.exit()  # FIXME only in dev. Have except for Ctrl+C to exit, none otherwise
    finally:
        reset_feedback()
    print('Done')


if __name__ == '__main__':
    main()
