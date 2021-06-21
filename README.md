# WhiteboardBot - Whiteboard capture, enhancement and sharing tool

WhiteboardBot implements a system that uses a Raspberry Pi 3/4, or similar
devices, to plug in one, or a set of cameras that would be able to capture
a white- or blackboard. This capture is triggered by a BLE remote.
After taking the picture, the files can automatically be sent to Slack
(to a specific channel or user), to one or several email addresses or
to a arbitrary mix of those.

There is also an optional enhancement feature for those pictures, such as
whiteboard enhancement, lens distortion fix and cropping. It also has an
optional feedback system through audio and visuals.

All those settings can be set, cameras, buttons and emails can be
dynamically added and removed. Buttons can be configured, so that pressing a
specific button will result in sharing through different channels.
This is done through a configuration menu, which is a website that is locally
reachable through whiteboardbot.local.

# Running the WhiteboardBot


# The guy responsible for this (mess)

Andreas Lindlbauer, formerly at the Center. 

This was my bachelors project and later a project while working at the center. 

There is also a bachelor thesis called "*Whiteboard Documentation, Enhancement and Sharing activated by a Wireless Remote*".
It is about the process of building it, but may give some insight into how I found out about something or why I implemented some of the stuff, and maybe why in that way that I did.
This thesis (hopefully) should be easy to get at the center. 
The people advising me were Verena Fuchsberger-Staufer, Martin Murer, Dorothé Smit, so they should have a copy.

I really liked working on this project so **please** contact me if there is something I forgot here or that you really can't figure out what to do or why I did something.
Don't break my heart and just throw the code away to start from scratch without considering this project first.
I made an effort to document and comment this project well.

You can reach me under these mail addresses:

- whiteboardbot.understress@aleeas.com

# How it works

For the general idea what it does and how it does that, see thesis (Whiteboard Documentation, Enhancement and Sharing activated by a Wireless Remote).

The code is also heavily commented which explains every part of the code.

## Here is an overview how it runs on the ODROID:

- The ODROID boots into TTY mode, allowing changes only over the command line.
- The bash script `whiteboardbot.sh` is being started automatically after boot.
  It is located in `/home/whiteboardbot/whiteboardbot.sh` along with the other code, log files, ... .
  - This script starts the actual program `whiteboardbot.py`. If the program crashes, it will put the error messages into a log file and restart the program.
  - The `slack_uploader.py` only is used for putting out API-Calls to Slack

## How to implement code changes

The code is not ready to be just put on the ODROID. You have to put in the credentials like Slack Token.
So that you don't have to do this by hand, I wrote two bash scripts called `copyAndArm.sh` and `copyAndTest.sh`.
In them you can change the credentials if you need to.
To use, you just have to use those bash scripts in the same folder as the code. 

It will make a folder `ProductionCode` for `copyAndArm.sh` and `TestCode` for`copyAndTest.sh` where the usable code will be in. 

# Maintenance

## Access

Access is possible through two ways:

1. Plug in screen and keyboard

2. Get access through SSH while in eduroam or other university network.
   - Access with: `ssh pi@<IP-address>`
     - The IP-address doesn't change much in the network, you can get it from the technichal assistants.
     - Password is also available there.
     - The `root`password is different but also available there.

## Sound

Sound is controlled over the program `alsamixer`.
Just type `alsamixer` and press enter, which will show a menu in the terminal where you can control the volume.

The sound files are in `/home/whiteboardbot/Music/sounds/` . If you want to change out the files without changing too much in the code, make sure they are `.wav` wave files. If you use a different file format, you might also have to use a different program than `aplay`.  

## Cameras

The cameras are plugged in over USB 3.0. Make sure that any cable or extension cord is compatible with that (The Lindy one isn't) and the port of any other device is also USB 3.0 else the pictures are not 4K anymore (They downgrade to 1080p).

If the pictures on the merged image are in the wrong order, either switch the USB-Plugs or look for occurrences of `/dev/video0` and `/dev/video1` in the code and switch them out with each other. This is the pointer to the webcam, so if anything else fails with that, it may be that one is now `/dev/video2` or none at all for whatever reason.

## Slack

The file `slack_uploader.py` is just a wrapper for the API-Calls to the slack bot. So it is used to send messages, upload files ect. but other than that nothing complicated is done there.
The Slack company itself provides a Slack client for Python which makes it easier to connect to the bot and issue API-calls.

## Log files

- `/var/log/whiteboardbot/bot.log` >>  Saves every output of the whiteboardbot, as well as error messages, including date and time

## Miscellaneous

- The ODROID has neither WiFi nor Bluetooth out of the box. There is a Bluetooth dongle plugged in but no WiFi.
- Over Ethernet it works fine, but if you change it to WiFi the IP-address will most likely change.
  - You COULD give it a permanent IP-Address. The IP-Address never changed on me, so I never bothered to do that. ~Sorry~

- I wasn't able to get this error on the new version, but that doesn't mean it's not there:
  - The Python script regulary crashes, because of the TEST-packets (see `whiteboardbot.py` code) .
    This is no problem for the whiteboard as it restarts the script and saves the error messages in `botlog.log`.
    Something about the signal from the Logitech POP crashes the Bluepy while it is scanning.
## Known Issues

### Errors

These can be found in the `botlog.log` together with the time they were issued.

#### Wrong answer from Slack:
(Not sure if this one is still happening)

```
Traceback (most recent call last):
  File "whiteboardbot.py", line 285, in <module>
    private = slackbot.check_ims(False)
  File "/home/whiteboardbot/slack_uploader.py", line 104, in check_ims
    messages = self.get_last_msg(channel["id"])  # Get the newest message posted
  File "/home/whiteboardbot/slack_uploader.py", line 79, in get_last_msg
    res = self.slack_client.api_call("im.history", channel=channel_id, count=1)
  File "/usr/local/lib/python3.5/dist-packages/slackclient/client.py", line 88, in api_call
    response_body = self.server.api_call(method, timeout=timeout, **kwargs)
  File "/usr/local/lib/python3.5/dist-packages/slackclient/server.py", line 338, in api_call
    response_json = json.loads(response.text)
  File "/usr/lib/python3.5/json/__init__.py", line 319, in loads
    return _default_decoder.decode(s)
  File "/usr/lib/python3.5/json/decoder.py", line 339, in decode
    obj, end = self.raw_decode(s, idx=_w(s, 0).end())
  File "/usr/lib/python3.5/json/decoder.py", line 357, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

Slack sometimes anwers with a string, html page or any other non-JSON response. This may be a bug of the Slack-API or for whatever reason may be even on purpose. 
I "fixed" it for now by retrying after an error, but sometimes it happens with other API-Calls. Either use the implemented retries at every API-Call, or tell Slack and find out what is going on there.

The actual problem is that Slack should answer only with JSON files, as they have a JSON decoder implmented into their own Slack client for python. This is not because of some error in my code. Yeah really, they made it like that. If you fixed this, please tell me (see e-mail address at beginning), I'm interested in how to get around that without some hack like `retry`.

# Features in progress

## More stable camera setup

Because the cameras are fixed on the ceiling by some flimsy wood board, the pictures aren't lined up perfectly.

My idea was to get:

- Two [Metal](https://www.bauhaus.at/gewindestangen/profi-depot-gewindestange-vz-48/p/10827379) [rods](https://www.bauhaus.at/gewindestangen/profi-depot-gewindestange-a2/p/10791773) from Bauhaus (Whiteboard Table)
- [Gewindeadapter](https://www.thomann.de/at/the_box_pro_stand_adapter_m6.htm)/screw thread adapter (Whiteboard Table)

Screw the rod to some (wooden or metal) plate, screw that plate to the ceiling. Screw that rod with the screw thread adapter to the camera. Watch out regarding the length of the table, the pipes/AC stuff and the projectors can interfere with the line of sight of the camera.

## Fix the Errors

See Known Issues

## Sound

To change the volume, use the command `alsamixer` over the shell, which will show a GUI inside the shell where you can change that. You may have to press `F6` to change to the correct sound card aka sound device that you want to change the volume of.
Maybe make this 

## Picture Quality

Except from the faulty alignment caused by the placement of the camera and settings of the distortion fixing (which also cuts the pictures as to fix alignment) there is also some glare, which could be fixed by putting on polarization filter foil on the camera.

When fixing the distortion fixing see https://www.imagemagick.org/Usage/distorts/#barrel and https://www.imagemagick.org/Usage/crop/#chop. 

Fixing the barrel distortion is a little bit strange. So according to the first link you need those variables. To get these variables you have to use [Hugin](http://hugin.sourceforge.net/download/). This will calculate the values from putting in several pictures taken with the cameras. Don't try to guess those values, that isn't really a possibility if you value your time and sanity. Here is a tutorial, hopefully it should do trick: http://hugin.sourceforge.net/tutorials/calibration/en.shtml . They changed their GUI just as I was finishing the fix. The cameras were moved and I wanted to do that after the final setup with the rods.

The way to set the parameters for cropping the images is also a little strange, so if you want to fix alignment here, read that second link.

## Nextcloud

See implementation from Portal project (-> Doro). The code there is based on this project, so it shouldn't be very hard to copy it into this here. More explanation is at that portal project.

