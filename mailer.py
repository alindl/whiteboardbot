"""
Send mail with reminder or pictures.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from email.header import Header
from email.utils import formatdate
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
import ssl
from os.path import basename
from time import strftime, localtime
import magic
from .read_config import get_key
from . import check_internet as wbci


def build_message(receiver_email, subject):
    """ Build message with the usual parts"""
    sender_email = get_key('Mail_Bot', 'address')

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ",".join(receiver_email)
    message["Subject"] = subject
    message['Date'] = Header(formatdate())
    return message


def send_reminder(receiver_email, msg):
    """Send reminder to for missed pictures that remain on memory and are unsent."""
    subject = "Missed whiteboard capture"
    sender_email = get_key('Mail_Bot', 'address')
    password = get_key('Mail_Bot', 'bot_password')

    # Create a multipart message and set headers
    message = build_message(receiver_email, subject)

    # Add body to email
    message.attach(MIMEText(msg, "plain"))
    text = message.as_string()

    # Log in to server using secure context and send email
    if wbci.internet():
        with SMTP_SSL(get_key('Mail_Bot', 'SMTP'),
                      get_key('Mail_Bot', 'port'),
                      context=ssl.create_default_context()) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)
            server.quit()
        print("sent mail reminder")
    else:
        raise ConnectionError('No Internet connection')


def send_mail(receiver_email, attachments):
    """Send mail with pictures to :params receiver_email:."""
    subject = "Whiteboard capture of " + strftime("%Y-%m-%d_%H:%M:%S", localtime())
    body = "Your whiteboard capture brought to you by your friendly neighbourhood WhiteboardBot!"
    sender_email = get_key('Mail_Bot', 'address')
    password = get_key('Mail_Bot', 'bot_password')

    # Create a multipart message and set headers
    message = build_message(receiver_email, subject)

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    # Now we attach the other files, including detecting type and setting appropriate headers
    file_type_getter = magic.open(magic.MAGIC_MIME_TYPE)
    file_type_getter.load()
    print(attachments)
    for attachment in attachments:
        maintype, subtype = file_type_getter.file(attachment).split('/')
        part = MIMEBase(maintype, subtype)
        part.set_payload(open(attachment, 'rb').read())
        encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{}"'.format(basename(attachment)))
        message.attach(part)

    text = message.as_string()

    # Log in to server using secure context and send email
    if wbci.internet():
        with SMTP_SSL(get_key('Mail_Bot', 'SMTP'),
                      get_key('Mail_Bot', 'port'),
                      context=ssl.create_default_context()) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, text)
            server.quit()
        print("sent mail")
    else:
        raise ConnectionError('No Internet connection')
