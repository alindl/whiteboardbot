"""Manages all uploads of image files.

Focuses the upload through Slack or Mail, depending on configuration.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from time import time
from .feedbacker import send_feedback, Message
from .mailer import send_mail, send_reminder
from .read_config import get_key, get_bool_key
from .slack_processor import SlackBot


def upload_to_slack(pictures, slack_bot):
    """Uploads the pictures to slack and a message depending on request situation.

    Checks the temp request file for a request and sends messages depending on,
    if there is a request.
    If the last request ran out, this person is getting notified.
    If not, tell person, trigger has been received.
    Upload to slack
    """
    channel = get_key('Slack', 'channel_name')

    request = slack_bot.queue.get()

    if request['request']:
        if time() <= request['ts']:
            message = "Received the trigger in time, you will get the photo!"
            channel = request['channel']

        else:
            # Hmm, this should never happen ... keep it in, just to be sure
            message = "Hey, sorry but you missed your request window, but I told you that."

        SlackBot.send_ephemeral_message(SlackBot,
                                        msg=message,
                                        user=request['user'],
                                        channel=request['channel'])

    # Make sure we pick the right file

    SlackBot.upload_file(SlackBot, pictures[0], channel)

    send_feedback(Message.UPLOAD)

    if get_bool_key('Output', 'enhance'):
        SlackBot.upload_file(SlackBot, pictures[1], channel)

    if request['request']:
        request['request'] = False
        request['user'] = None
        request['real_name'] = None
        request['channel'] = None
        request['ts'] = float(get_key('Slack', 'request_period'))
    slack_bot.queue.put(request)
    print("after slack upload")


def upload_by_mail(pictures, mail_list):
    """Gather mail list, send task to upload."""
    addresses = []
    print(mail_list)
    # Mail can be activated but not mapped to this button
    if len(mail_list) > 0:
        print("mail list has mails in it")
        for mail_num in mail_list:
            addresses.append(get_key(mail_num, "address"))
        print("after action")

        send_mail(addresses, pictures)
    else:
        print("Mail activated but no mails choosen on this button")
    print("after mail upload")


def get_upload_targets():
    """Construct and return unset dict of targets."""
    # Possible actions:
    #   normal              All available targets
    #   all_mail            All available emails
    #   [slack]{, Mail#}    Only specific emails and/or slack
    upload_targets = {'slack': False}
    for mail in range(int(get_key('Output', 'num_mail'))):
        upload_targets['mail_' + str(mail)] = False

    return upload_targets


def set_upload_targets(actions):
    """Translate meta targets into actual targets, set them accordingly and return."""
    upload_targets = get_upload_targets()
    slack = get_bool_key('Output', 'slack')
    email = get_bool_key('Output', 'mail')
    # A little bit long but very explicit about what should happen
    if actions[0] == "normal":
        if slack:
            upload_targets['slack'] = True
        if email:
            for mail in range(int(get_key('Output', 'num_mail'))):
                upload_targets['Mail' + str(mail)] = True
    elif actions[0] == "all_mail":
        if email:
            for mail in range(int(get_key('Output', 'num_mail'))):
                upload_targets['Mail' + str(mail)] = True
    else:
        for action in actions:
            if action in upload_targets:
                upload_targets[action] = True

    return upload_targets


def save_all_targets(all_targets, targets):
    """Set actual targets from button to dict."""
    # FIXME: Seems a bit convoluted.
    for action, activated in targets.items():
        all_targets[action] = activated or all_targets[action]
    return all_targets


def send_reminders(all_targets):
    """Send reminders for unsent pictures because of internet outage."""
    mail_list = []
    msg = "There are unsent pictures on the Whiteboardbot SD-Card, \
            because of an Internet outage on the last trigger. \
            They are automatically going to get deleted in 30 days."
    for action, activated in all_targets.items():
        if activated:
            if action == 'slack':
                SlackBot.send_message(SlackBot, msg, attachment=None,
                                      channel=get_key("Slack", "channel_name"))
            else:
                mail_list.append(action)
    if len(mail_list) > 0:
        addresses = []
        print(mail_list)
        for mail_num in mail_list:
            addresses.append(get_key(mail_num, "address"))
        # TODO check if this handover worked correctly
        send_reminder(addresses, msg)

    return time()


def upload(button, pictures, enhancer=None, slack_bot=None):
    """Check upload targets and upload accordingly."""
    # TODO Test this

    # bool(int('1'))) ? I know, I'm fun at parties
    email = get_bool_key('Output', 'mail')

    actions = eval(button['action'])

    upload_targets = set_upload_targets(actions)

    mail_list = []
    # Why trust positions of file names, if we could trust,
    # that files ready for upload are always *.jpg
    uploads = []

    for picture in pictures:
        if picture.find(".jpg") != -1:
            uploads.append(picture)
            if enhancer is not None:
                enhancer.join()  # Waits until enhancer terminates

    for action, activated in upload_targets.items():
        if activated:
            if action == 'slack':
                upload_to_slack(uploads, slack_bot)
            else:  # Can only be either slack or mail
                mail_list.append(action)
    if email:
        upload_by_mail(uploads, mail_list)

    print("done uploading")
