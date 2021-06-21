"""Simple interface to read from the config file

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

from configparser import ConfigParser

CONFIG_FILE = "/etc/whiteboardbot.conf"


def get_config():
    """Load config file."""
    config = ConfigParser()
    config.read(CONFIG_FILE)
    # config.read("whiteboardbot.ini")
    return config


def get_key(section, key):
    """Get key from config file."""
    return get_config().get(section, key)


def get_bool_key(section, key):
    """Get key from config file."""
    return get_config().getboolean(section, key)


def has_section(section):
    """Get section from config file."""
    return get_config().has_section(section)


def get_section(section):
    """Get section from config file."""
    conf = get_config()
    if conf.has_section(section):
        return get_config().items(section)
    return False


def write_config(config):
    """Get section from config file."""
    try:
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    except IOError:
        return False
    return True
