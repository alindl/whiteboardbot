"""Manages all interactions with Slack.

.. such as sending normal or ephemeral messages and uploading files.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from multiprocessing import Queue
from threading import Event, Thread
# import asyncio
from time import sleep, time
from slack import WebClient
from slack.errors import SlackApiError
from .read_config import get_key
from .rtm import RTMBot
from .feedbacker import send_feedback, Message


class SigBot(Thread):
    """Handles the reminder functionality, after a private pic was requested"""
    signal = None
    queue = None
    slack_bot = None

    def __init__(self, shared_queue, shared_signal, shared_slack, *args, **kwargs):
        super(SigBot, self).__init__(*args, **kwargs)
        # TODO super(...) needed instead of super()?
        self.signal = shared_signal
        self.queue = shared_queue
        self.slack_bot = shared_slack

    def run(self):

        while True:
            self.signal.wait()
            send_feedback(Message.UPLOAD)
            old_request = self.queue.get(block=False)
            self.queue.put(old_request, block=False)
            # print("starting to check", file=open("/tmp/output.txt", "a"))
            # print(old_request, file=open("/tmp/output.txt", "a"))

            # sleep(float(get_key('Slack', 'request_period')))

            some_request = old_request

            sleep(1)
            while some_request['request'] and float(some_request['ts']) >= float(time()):
                if not self.queue.empty():
                    some_request = self.queue.get(block=False)
                    self.queue.put(some_request, block=False)
                    # print("still checkin", file=open("/tmp/output.txt", "a"))
                    # print(some_request, file=open("/tmp/output.txt", "a"))
                sleep(1)

            if not self.queue.empty():
                new_request = self.queue.get()

                print("Waited long enough")

                if new_request['request'] and (old_request['user'] == new_request['user']):

                    message = "Hey, sorry but you missed your request window!"

                    self.slack_bot.send_ephemeral_message(
                        msg=message,
                        user=old_request['user'],
                        channel=old_request['channel']
                    )

                    new_request['request'] = False
                    new_request['user'] = None
                    new_request['real_name'] = None
                    new_request['channel'] = None
                    new_request['ts'] = float(get_key('Slack', 'request_period'))
                    while not self.queue.empty():
                        self.queue.get(block=False)
                    self.queue.put(new_request)
                    print("Done with resetting")
            self.signal.clear()


class SlackBot:
    """Class that represents the Bot in the Slack workspace."""
    # FIXME Do we really need to have it here, if it's already implemented in init?
    slack_client = WebClient(token=get_key("Slack", "token"))
    rtmbot = None
    sig_check = None
    queue = Queue()
    signal = Event()
    queue.put({'request': False,
               'user': None,
               'real_name': None,
               'channel': None,
               'ts': float(get_key('Slack', 'request_period'))
               })

    def __init__(self):
        """Init the connection to the webclient."""
        self.rtmbot = RTMBot(self.queue, self.signal)
        self.rtmbot.start()
        sig_check = SigBot(self.queue, self.signal, self)
        sig_check.start()

    def send_message(self, msg, attachment=None, channel=get_key("Slack", "channel_name")):
        """Wrapper for sending text messages to people or channels."""
        try:
            # API CALL chat.postMessage has now a limit of 1 per second per channel
            res = self.slack_client.chat_postMessage(channel=channel, text=msg,
                                                     attachments=attachment,
                                                     as_user=False)
            if not res.get('ok'):
                print(res.get('error'))
                print(res.get('response_metadata'))
        except SlackApiError:  # No internet or Slack is down
            print("Couldn't reach Slack workspace")

    def send_ephemeral_message(self, msg, user, link_names=False,
                               channel=get_key("Slack", "channel_name")):
        """Wrapper for sending ephemeral text messages to people or channels."""
        # Plain send text method
        try:
            # API CALL chat.postEphemeral has now a limit of 100 per minute per channel
            res = self.slack_client.chat_postEphemeral(channel=channel,
                                                       text=msg,
                                                       user=user,
                                                       as_user=False,
                                                       link_names=link_names)
            i = 0
            while i < 5 and not res.get('ok'):
                i += 1
                print(res.get('error'))
                print(res.get('response_metadata'))
                print("EPH MESSAGE SENDING FAILED, try again")
                res = self.slack_client.chat_postEphemeral(channel=channel,
                                                           text=msg,
                                                           user=user,
                                                           as_user=False,
                                                           link_names=link_names)
            if i >= 5:
                print("Tried too many times, abort")
                raise ConnectionError("Couldn't reach Slack")
        except SlackApiError:  # No internet or Slack is down
            print("Couldn't reach Slack workspace")

    def upload_file(self, filename, channel):
        """Upload :params filename: to :params channel:."""
        # API CALL files.upload has now a limit of 20 per minute
        try:
            with open(filename, 'rb') as file_data:
                res = self.slack_client.files_upload(filename=filename,
                                                     channels=channel,
                                                     file=file_data)
                i = 0
                while i < 5 and not res.get('ok'):
                    i += 1
                    print(res.get('error'))
                    print(res.get('response_metadata'))
                    print("UPLOAD FAILED, try again")
                    res = self.slack_client.files_upload(filename=filename,
                                                         channels=channel,
                                                         file=file_data)
                if i >= 5:
                    print("Tried too many times, abort")
                    raise ConnectionError("Couldn't reach Slack")

        except SlackApiError:  # No internet or Slack is down
            print("Couldn't reach Slack workspace")
        # Reset request


if __name__ == '__main__':
    SlackBot()
