"""Sends audio and visual feedback.

Defines an enum of different messages and sends out the configured audio as defined in conf.
Visual signals are just the same for every message, but this should be extended in the future.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from subprocess import Popen, PIPE
from threading import Thread
from enum import Enum
from time import sleep
from . import read_config as wbconfig
import RPi.GPIO as GPIO  # Import Raspberry Pi GPIO library


class Message(Enum):
    """Define the different type of messages as enum."""
    TRIGGER = "trigger"
    REQUEST = "request"
    ERROR = "error"
    UPLOAD = "upload"
    CAMERA = "camera"
    READY = "ready"


def send_feedback(message):
    """Depending on configuration, send out different feedback."""
    if wbconfig.get_bool_key("Output", "audio"):
        play_sound(message)
    if wbconfig.get_bool_key("Output", "visual"):
        light = Thread(target=flash_light, args=[message])
        light.start()


def play_sound(sound):
    """Play specific sound, depending on message and configuration."""
    Popen(["aplay", "-D", "sysdefault",
           wbconfig.get_key("Other", "sounds_dir") + '/' +
           wbconfig.get_key("Sound_Sources", sound.value)],
          stdout=PIPE, stderr=PIPE)


def flash_signal(message):
    """Flash LED rapidly 10 times"""
    GPIO.setwarnings(False)  # Ignore warning for now
    GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
    # Set pin 8 to be an output pin and set initial value to low (off)
    led_fb_pin = 8
    GPIO.setup(led_fb_pin, GPIO.OUT, initial=GPIO.LOW)
    for _ in range(10):  # Run 3 times
        GPIO.output(led_fb_pin, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(led_fb_pin, GPIO.LOW)
        sleep(0.1)


def flash_light(state):  # pylint: disable=unused-argument
    # TODO I have no different patterns for the LED right now
    """Flash LED on Raspberry Pi, kind of a stub at the moment."""
    # TODO implement different kinds of visual feedback
    #     For now, it's just blinking 3 times in any case
    GPIO.setwarnings(False)  # Ignore warning for now
    GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
    # Set pin 8 to be an output pin and set initial value to low (off)
    led_fb_pin = 8
    GPIO.setup(led_fb_pin, GPIO.OUT, initial=GPIO.LOW)
    for _ in range(3):  # Run 3 times
        GPIO.output(led_fb_pin, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(led_fb_pin, GPIO.LOW)
        sleep(0.4)


def reset_feedback():
    """Reset LED, as there's a but sometimes, where the LED keeps being lit"""
    # TODO Check again if this is an issue with the PowerLEDs
    GPIO.setwarnings(False)  # Ignore warning for now
    GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering
    # Set pin 8 to be an output pin and set initial value to low (off)
    led_fb_pin = 8
    GPIO.setup(led_fb_pin, GPIO.OUT, initial=GPIO.LOW)
    GPIO.output(led_fb_pin, GPIO.LOW)
