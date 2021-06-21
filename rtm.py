"""Manages all interactions with Slack.

.. such as sending normal or ephemeral messages and uploading files.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from time import time
from threading import Thread
import asyncio
from slack import RTMClient
from slack.errors import SlackApiError
from .read_config import get_key


class RTMBot(Thread):
    """Thread that checks Slack for incoming requests"""
    # slack_client = WebClient(token=get_key("Slack", "token"))
    # slack_bot = None
    queue = None
    signal = None

    def __init__(self, shared_queue, shared_signal, *args, **kwargs):
        super(RTMBot, self).__init__(*args, **kwargs)
        # TODO is super(...) needed instead of super()? I'm not sure
        # self.slack_bot = shared
        self.queue = shared_queue
        self.signal = shared_signal

    def run(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        # loop = asyncio.get_event_loop()
        # rem = Thread(target=reminder, args=(self.queue, ))
        # rem.start()
        rtm_client = RTMClient(token=get_key("Slack", "token"))
        rtm_client.on(event="message", callback=self.message)
        # rtm_client = RTMClient(token=get_key("Slack", "token"), run_async=True, loop=loop)
        # rtm_client._event_loop = loop
        print("ready?")
        rtm_client.start()
        # asyncio.run(rtm_client.start())
        # loop.run_until_complete(rtm_client.start())
        print("rtm running")

    # @RTMClient.run_on(event="message")
    def message(self, **payload):
        """Go through every message, check if '!snap' is mentioned, safe this data.

        * Every time a message gets through the system, there's a scan for the substring "!snap"
        * If there is such a message, save user and channel.
        * Make or get the request file contents
        * Send an ephemeral apology if some other person already requested
        * Send an ephemeral message, to the person requesting, save data to temp request file
        * Save data of the requester into requester file

        Requests, that have been unfulfilled, are discarded through checking the timestamp.
        Fulfilled requests are dealt with at the uploader (uploader.py), which erases the
        request date in the temp request file after uploading.

        """

        # asyncio.get_event_loop().run_in_executor(None, process_message(payload, self.queue)),
        # asyncio.ensure_future(process_message(payload, self.queue), loop=asyncio.get_event_loop())

        data = payload['data']
        web_client = payload['web_client']
        # request = RTMBOT.slack_bot.request
        # request = self.rtm_client.request
        # global REQUEST
        # request = REQUEST
        request = self.queue.get()
        remind = False
        # request = {}
        # if not slack_bot:
        #    request = {}
        # else:
        #    request = self.slack_bot.request

        print(data)
        if 'text' in data and '!snap' in data['text']:
            print("okay nice")
            if not request:
                request['request'] = False
                request['user'] = None
                request['real_name'] = None
                request['channel'] = None
                request['ts'] = float(get_key('Slack', 'request_period'))
                # request was unset
                # REQUEST = request

            print(request)
            if request['request'] and \
                    time() < request['ts']:
                user_name = get_user(web_client, request['user'])['name']

                message = "Sorry, " + \
                          request['real_name'] + "(@" + user_name + ")" + \
                          " already requested the next photo! Try again in " + \
                          str(int(float(request['ts']) - time())) + \
                          " seconds."

                send_ephemeral_message(web_client,
                                       msg=message,
                                       user=data.get('user'),
                                       channel=data.get('channel'),
                                       link_names=True
                                       )

            if not request['request']:
                print("nothing to see here")
                # TODO Check if it's a good idea to put request_period in ts
                # NOTE Implement a way to set sinks through request
                #      See worklog on 2020-04月09日
                message = "Press the trigger within " + str(int(float(request['ts']))) + \
                          " seconds and you will receive the picture!"

                send_ephemeral_message(web_client,
                                       msg=message,
                                       user=data.get('user'),
                                       channel=data.get('channel'),
                                       )

                real_name = get_user(web_client, data.get('user'))['real_name']

                # we need this, because the user should be notified from the private channel
                im_channels = web_client.conversations_list(types='im',
                                                            limit=999)['channels']
                requester_channel = ""
                for channel in im_channels:
                    if channel['user'] == data.get('user'):
                        requester_channel = channel['id']
                        break

                request['request'] = True
                request['user'] = data.get('user')
                request['real_name'] = real_name
                request['channel'] = requester_channel
                # request['ts'] = float(request['ts']) + float(data.get('ts'))
                request['ts'] = float(get_key('Slack', 'request_period')) + float(time())
                # REQUEST = request

                # Strangely, everything works until this point
                print("Now remind me")
                # reminder(self.queue)
                remind = True
            self.queue.put(request)
            print("done with message")
            # self.signal.set()
            if remind:
                self.signal.set()
                # remind = False
                print("Reminder done lol")


def get_user(slack_client, user_id):
    """Wrapper for sending ephemeral text messages to people or channels."""
    # API CALL files.upload has now a limit of 20 per minute
    try:
        res = slack_client.users_info(user=user_id)
        if not res.get('ok'):
            print(res.get('error'))
            print(res.get('response_metadata'))
        else:
            return res['user']
        return False
    # FIXME this needs specified exception
    except SlackApiError:  # No internet or Slack is down
        print("Couldn't reach Slack workspace")


def send_ephemeral_message(slack_client, msg, user, link_names=False,
                           channel=get_key("Slack", "channel_name")):
    """Wrapper for sending ephemeral text messages to people or channels."""
    # Plain send text method
    try:
        # API CALL chat.postEphemeral has now a limit of 100 per minute per channel
        res = slack_client.chat_postEphemeral(channel=channel,
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
            res = slack_client.chat_postEphemeral(channel=channel,
                                                  text=msg,
                                                  user=user,
                                                  as_user=False,
                                                  link_names=link_names)
        if i >= 5:
            print("Tried too many times, abort")
            raise ConnectionError("Couldn't reach Slack")
    except SlackApiError:  # No internet or Slack is down
        print("Couldn't reach Slack workspace")
