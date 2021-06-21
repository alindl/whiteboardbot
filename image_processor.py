"""Manages all interactions with the image files and cameras.

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

import subprocess
from threading import Thread
from time import strftime, localtime
from .feedbacker import send_feedback, Message
from .read_config import get_key, get_bool_key


def enhance(picture):
    """Starts enhancing thread, to allow for multithreading. Returns thread."""

    enhancer = Thread(target=enhance_thread, args=(picture,))
    print("before start")
    enhancer.start()
    print("after start")
    return enhancer, picture[:-4] + "_ENHANCED.jpg"


def enhance_thread(file_name):
    """Enhance :params file_name: given."""
    # We now enhance the picture to be more legible through applying Difference of Gaussian
    print(file_name)
    # TODO test this
    _ = subprocess.run(["bash", "/usr/lib/whiteboardbot/enhancer.sh", file_name,
                        file_name[:-4] + "_ENHANCED.jpg"
                        ],
                       shell=False, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("finished subprocess")
    # progress.set()


def remove_pictures(pictures):
    """Remove all pictures."""
    subprocess.run(["rm"] + pictures,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def take_picture(num, file_name):
    """Take a picture according to config. Name it as :param file_name:. Return Thread."""
    cam = subprocess.Popen(["fswebcam", "-d", get_key('Cam' + str(num), 'src'),
                            "-p", "MJPEG", "-r",
                            get_key('Cam' + str(num), 'resolution'),
                            "--frames", "20", "--no-banner", "-D", "1", file_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cam


def fix_distortion(file_name, metrics):
    """Fix distortion, return thread.

    Fix distortion produced by camera on :param file_name: according to :param metrics:.
    Return thread that allows checking, if fixing is done.
    """
    pic = subprocess.Popen(["convert", file_name, "-virtual-pixel", "black", "-distort", "Barrel",
                            metrics, file_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # "-0.0145 0.0 0.07", "-crop", metrics, file_name],
    return pic


def crop_pic(file_name, metrics):
    """Crop :param file_name: according to :param metrics:. Return thread."""
    pic = subprocess.Popen(["convert", file_name, "-virtual-pixel", "black",
                            "-crop", metrics, file_name],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return pic


# Does exactly what the method name tells us
#   private_channel   = Is the direct message channel, if empty string -> public channel
def make_pic():
    """Main function to run through picture taking workflow. Return list of pictures.

    * Name files according to date and time, save them as png.
    * Save filenames in list of pictures
    * Take pictures, wait for them to be done.
    * Fix distortion and/or cropping according to config, wait for them to be done.
    * Append into one file if needed, return list of all pictures
    """
    print("preset pic stuff")
    date = strftime("%Y-%m-%d_%H%M%S", localtime())
    file_name = "/tmp/" + date + ".png"

    # If there's trouble with the order of the files,
    # check in which order the cameras link to video0 and video1 for example.
    # This could result in a flipped order of files

    num_cams = int(get_key('Output', 'num_cameras'))

    pictures = []
    cams = []
    print("actually taking pictures")
    for cam in range(num_cams):
        pictures.append("/tmp/" + date + "_" + str(cam) + ".png")
        cams.append(take_picture(cam, pictures[cam]))

    # This loop will run as long as a cam is still running
    for cam in cams:
        print("waiting for cams")
        cam.wait()

    # Make camera click sound AFTER BOTH pictures have been made
    print("done waiting")
    send_feedback(Message.CAMERA)

    fix_dist = get_bool_key('Output', 'fix_distortion')
    fix_crop = get_bool_key('Output', 'fix_crop')

    print("fixing")
    # Fix the distortion and/or crop the pictures to be ready for appending
    if fix_dist:
        # Going though those cameras with a for to get that multithreading
        pics_to_fix = []
        for pic in range(num_cams):
            metrics = get_key('Cam' + str(pic), 'correction_metrics')
            pics_to_fix.append(fix_distortion(pictures[pic], metrics))

        # This loop will run as long as one fixing process is still running
        for pic in pics_to_fix:
            pic.wait()
    print("done fixing")

    print("cropping")
    if fix_crop:
        pics_to_fix = []
        for pic in range(num_cams):
            metrics = get_key('Cam' + str(pic), 'cropping_metrics')
            pics_to_fix.append(crop_pic(pictures[pic], metrics))

        # This loop will run as long as one cropping process is still running
        for pic in pics_to_fix:
            pic.wait()
    print("done cropping")

    print("appending")
    # Append into one
    if num_cams > 1:
        subprocess.run(['convert'] + pictures + ['+append', file_name],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    else:
        # Don't use append on one picture, it will just increase file size
        print(pictures)
        subprocess.run(['mv'] + pictures + [file_name],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        pictures.pop()

    pictures.append(file_name)

    print("done appending")
    print("done with picture")
    print(pictures)

    # We return the originals + the finished picture
    return pictures, file_name


def convert_png_to_jpg(in_file):
    """Simply convert PNG to JPG."""
    out_file = in_file[:-3] + "jpg"
    print("Start converting to jpg")
    subprocess.run(["convert", in_file, out_file],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print("Done converting to jpg")
    return out_file
