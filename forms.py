"""
Backend for Config webserver

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

import re
import subprocess
from flask import escape, Markup
from flask_wtf import FlaskForm
from flask_babel import gettext as _, ngettext, gettext
from wtforms import Form, FieldList, FormField, SelectField, \
    StringField, BooleanField, SubmitField, PasswordField, \
    validators, ValidationError, SelectMultipleField, HiddenField
from wtforms.fields.html5 import IntegerRangeField
# from . import read_config as wbconf
# NOTE Why do I have to NOT use the dot notation here???
import read_config as wbconf

# NOTE Security real talk:
#      We are saving the password for the bot mail account in plain text.
#      You have bigger issues to deal with, if somebody has access to the SoC that is running
#      this code as that SoC and account should only be accessible from the inside network.
#      Similar issue with the login for the edit page. This is not about security, it's about
#      making sure that users that don't know any better don't accidentally change something.
#      It hurts me to deploy something like that though, but I didn't find a better way 🙃

INFO_ICON = "fill='currentColor' class='bi bi-info-circle' viewBox='0 0 16 16'>" \
            "<path d='M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z'></path>" \
            "<path " \
            "d='m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 " \
            "1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 " \
            "0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z'></path>" \
            "</svg>"


# VALIDATORS

# Yeah, can't change that, would throw an error if I removed the argument
# pylint: disable=unused-argument
# noinspection PyUnusedLocal
def check_if_output_activated(form, field):
    """ This checks if at least one sink is activated"""
    if not (form.slack_bool.data or form.mail_bool.data):
        raise ValidationError(_('Either E-Mail or Slack must be activated'))


def validate_sound(form, field):
    """ Validate if sound file names are valid"""
    audio_check = form.audio_bool.data
    if audio_check:
        pattern = re.compile(r"^/?([A-z0-9-_+]+/)*([A-z0-9]+\.(wav))$")
        # pattern = re.compile(r"^?([A-z0-9-_+]+)*([A-z0-9]+\.(wav))$")
        if pattern.match(field.data) is None:
            raise ValidationError(_("Must be a valid filename ending .wav"))


def validate_action(form, field):
    """Validate the action field of the form"""
    singles = ['normal', 'all_mail']
    if field.data and len(field.data) > 1 and any(item in field.data for item in singles):
        if all(item in field.data for item in ['all_mail', 'slack']):
            field.data = ['normal']
        else:
            raise ValidationError(_('Your choices overlap indirectly. Make sure you picked the right ones.'))
    # NOTE We could check, if all mail were selected, to switch to all mail, but maybe the user did it on accident.


def validate_mails(form, field):
    """ Validate if mail configs are valid"""
    num_check = form.num_mail.data
    if isinstance(num_check, int):
        activated_fields = range(len(field))
        pattern = re.compile(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}$")
        used_mails = []
        for i in activated_fields:
            if num_check > i:
                if pattern.match(field[i].data['address']) is None:
                    field.errors.append(
                        {'address': [_('Enter a valid E-Mail Address')]})
                if field[i].data['address'] in used_mails:
                    field.errors.append({'address': [_('E-Mail already in use.')]})
                else:
                    used_mails.append(field[i].data['address'])


def validate_password(form, field):
    """ Validate that the password is longer than 8 chars and both the same"""
    pattern = re.compile(r".{8,}")
    if len(field.data) < 8 or pattern.match(field.data) is None:
        raise ValidationError(
            _('Password should be at least 8 characters long.'))
    if field.data != form.password_check.data:
        raise ValidationError(_("Passwords don't match"))


# FIELD GENERATORS

def generate_slack_channel_name_field():
    # NOTE: Wrongly doesn't match a channel name, ending in "-" or "_".
    #       Through this regex though, rightfully so, "-" and "_" are allowed at the beginning,
    #       but ONLY if num or letters follow
    #       Fixing this is not worth the effort
    return StringField(
        Markup(_("Slack channel") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('The Slack channel where whiteboard images can be sent to') + "' " +
               INFO_ICON),
        render_kw={"placeholder": _("demochannel")}
    )


def generate_sound_fields():
    return StringField(
        _('Trigger sound effect'),
        validators=[validate_sound],
        render_kw={"placeholder": "trigger_notification.wav"}
    ), StringField(
        _('Request sound effect'),
        validators=[validate_sound],
        render_kw={"placeholder": "notify_request.wav"}
    ), StringField(
        _('Error sound effect'),
        validators=[validate_sound],
        render_kw={"placeholder": "error_sound.wav"}
    ), StringField(
        _('Upload sound effect'),
        validators=[validate_sound],
        render_kw={"placeholder": "uploaded.wav"}
    ), StringField(
        _('Camera sound effect'),
        validators=[validate_sound],
        render_kw={"placeholder": "camera_click.wav"}
    ), StringField(
        _('Ready sound effect'),
        validators=[validate_sound],
        render_kw={"placeholder": "system_start_ready.wav"}
    )


def generate_mails_field(form):
    return FieldList(
        FormField(form, label=_("Mail Address")),
        min_entries=0,
        validators=[validate_mails]
    )


def generate_buttons_field(form):
    return FieldList(
        FormField(form, label=""),
        min_entries=1
    )


def generate_slack_bool_field():
    return BooleanField(
        Markup(_("Use Slack") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('Use Slack as a possible way to send pictures') + "' " +
               INFO_ICON),
        [check_if_output_activated]
    )


def generate_mail_bool_field():
    return BooleanField(
        Markup(_("Use e-mail") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('Use e-mail as a possible way to send pictures') + "' " +
               INFO_ICON),
        [check_if_output_activated]
    )


def generate_read_only_field():
    return HiddenField(
        _('Read only mode')
    )


def generate_status_fields():
    return HiddenField(
        _('Status of the whole whiteboardbot system')
    ), HiddenField(
        _('Status of BLE (Bluetooth Low Energy for buttons)')
    ), HiddenField(
        _('Status of Internet connection')
    )


def generate_password_fields():
    return PasswordField(
        _('Password of user'),
        render_kw={"placeholder": _("A solid password that is at least 8 characters long")},
        validators=[validate_password]
    ), PasswordField(
        _('Repeat password'),
        render_kw={"placeholder": _("Repeat password that same password")},
        validators=[validate_password]
    )


def generate_num_of_things_field(thing):
    return IntegerRangeField(
        _('Number of ' + thing)
    )


def generate_timevar_field():
    return HiddenField(
        Markup(_("Last push") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _(
            "This is the timestamp of the last button press (or some random signal from the button)")
               + "'" + INFO_ICON),
        # validators=[validators.NumberRange(min=1577833200.000000000)]
        # It has to be at least the year 2020
    )


def generate_action_field(choices):
    return SelectMultipleField(
        Markup(_("sends images to:") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _("This is where pictures are going to be sent to. Hold shift to select multiple entries, \
            but make sure that your choices don&#39t overlap.") + "'" +
               INFO_ICON),
        choices=choices,
        validators=[validate_action]
    )


def generate_button_name_field():
    return StringField(
        Markup(_("Name of button") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _("Pick a memorable name for this button. \
               This is for you to figure out which button does what.") + "'" +
               INFO_ICON),
        render_kw={"placeholder": _("Yellow button")}
    )


def generate_audio_bool_field():
    return BooleanField(
        Markup(_("Audio feedback") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('Audio signals that indicate progress. \
               Only editable by the admin.') + "' " +
               INFO_ICON),
    )


def generate_visual_bool_field():
    return BooleanField(
        Markup(_("Visual feedback") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('Visual signals that indicate progress. \
               Only editable by the admin.') + "' " +
               INFO_ICON),
    )


# MISC

def generate_mail_choices(choices):
    ml_num = 0
    while wbconf.has_section("Mail" + str(ml_num)):
        tmp_ml = wbconf.get_section('Mail' + str(ml_num))
        choices.append(
            ("mail_" + str(ml_num), _("Send to mail address: ") + tmp_ml[0][1]))
        ml_num += 1


class LimitedButtonForm(Form):
    """Subform that represents the arbitrary number of buttons.
    """

    # It is an iterable in this case though
    # pylint: disable=not-an-iterable
    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(LimitedButtonForm, self).__init__(*args, **kwargs)

    read_only = generate_read_only_field()

    btn_name = generate_button_name_field()

    mac = HiddenField(
        Markup(_("MAC address "))
    )

    timevar = generate_timevar_field()

    choices = [('normal', _('Send to all activated outputs')), ('slack', _('Send to Slack')),
               ('all_mail', _('Send to all mail addresses'))]

    generate_mail_choices(choices)

    action = generate_action_field(choices)


class ViewButtonForm(Form):
    """Subform that represents the arbitrary number of buttons for ViewForm
    """

    # It is an iterable in this case though
    # pylint: disable=not-an-iterable
    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(ViewButtonForm, self).__init__(*args, **kwargs)

    read_only = generate_read_only_field()

    btn_name = generate_button_name_field()

    mac = HiddenField(
        Markup(_("MAC address "))
    )

    timevar = generate_timevar_field()

    choices = [('normal', _('Send to all activated outputs')), ('slack', _('Send to Slack')),
               ('all_mail', _('Send to all mail addresses'))]

    generate_mail_choices(choices)

    action = generate_action_field(choices)


class ButtonForm(Form):
    """Subform that represents the arbitrary number of buttons.
    """

    # It is an iterable in this case though
    # pylint: disable=not-an-iterable
    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(ButtonForm, self).__init__(*args, **kwargs)

    read_only = generate_read_only_field()

    btn_name = generate_button_name_field()

    mac = StringField(
        Markup(_("MAC address") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _("MAC address of this button. It&#39s not that easy to figure out. \
               Some print it on the package, but there&#39s a chance that you have to sniff it out.") + "' " +
               INFO_ICON),
        description=escape(_("Enter the valid MAC address of the button. No duplicates in the list")),
        render_kw={"placeholder": "AB:12:CD:34:EF:56"}
    )

    timevar = generate_timevar_field()

    choices = [('normal', _('Send to all activated outputs')), ('slack', _('Send to Slack')),
               ('all_mail', _('Send to all mail addresses'))]

    generate_mail_choices(choices)

    action = generate_action_field(choices)


class CamForm(Form):
    """Subform that represents the arbitrary number of buttons.
    """

    def __init__(self, *args, **kwargs):
        super(CamForm, self).__init__(*args, **kwargs)

    read_only = generate_read_only_field()

    cam_choices = []

    cams = subprocess.run("ls /sys/class/video4linux".split(), check=True,
                          capture_output=True).stdout.decode("utf-8").rstrip().split('\n')

    cam_srcs = list(map(lambda x: "/dev/" + x, cams))

    cam_name_srcs = list(
        map(lambda x: "/sys/class/video4linux/" + x + "/name", cams))

    # for x in range(len(cam_name_srcs)):
    for x, _ in enumerate(cam_name_srcs):
        # NOTE We could also fetch resolution from cam, but we would need to fetch them beforehand
        actual_name = subprocess.run(['cat', cam_name_srcs[x]], check=True,
                                     capture_output=True).stdout.decode("utf-8").rstrip()
        cam_choices.append((cam_srcs[x], actual_name))

    src = SelectField(
        Markup(gettext("Camera") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + gettext(
            "Choose the specific camera. If they have the same name, the first one is usually the correct one.") + "'" +
               INFO_ICON),
        description=escape(gettext("This source is already in use")),
        choices=cam_choices
    )

    resolution = StringField(
        Markup(gettext("Resolution") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + gettext("Choose the resolution that is supported by this camera") + "'" +
               INFO_ICON),
        description=escape(gettext("Resolution should be NUMBERxNUMBER")),

        render_kw={"placeholder": "1920x1080"}

        # Getting the real possible resolutions is totally overkill to do in python
    )

    distMetrics = StringField(
        Markup(gettext("Distortion metrics") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + gettext("Parameters to fix lens distortion, such as -0.0145 0.0 0.07 \
                       and an optional fourth number which is automatically calculated though.") + "'" +
               INFO_ICON),
        description=escape(gettext("Parameters should be decimal numbers A B C [D]")),
        render_kw={"placeholder": "-0.0145 0.0 0.07"}
        # validators=[check_dist]
    )

    cropMetrics = StringField(
        Markup(gettext("Cropping metrics") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + gettext(
            'Parameters should be\nLENGTHxHEIGHT[+/-]X_OFFSET[+/-]Y_OFFSET, such as 1920x1080-0+40') + "' " +
               INFO_ICON),
        description=escape(gettext("Parameters should be \
                NUMBERxNUMBER[+/-]NUMBER[]+/-]NUMBER")),
        render_kw={"placeholder": "1920x1080-0+40"}
        # validators=[check_crop]
    )


class MailForm(Form):
    """Subform that represents the arbitrary number of mail addresses.
    """

    # It is an iterable in this case though
    # pylint: disable=not-an-iterable
    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(MailForm, self).__init__(*args, **kwargs)

    read_only = generate_read_only_field()

    address = StringField(
        '', description=escape(gettext("Enter a valid and unique email address")),
        render_kw={"placeholder": _("jane.smith@example.com")}

    )


class UserForm(Form):
    """Subform that represents the arbitrary number of users.
    """

    # It is an iterable in this case though
    # pylint: disable=not-an-iterable
    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

    read_only = generate_read_only_field()

    username = HiddenField(
        _('Username'),
    )


class ViewForm(FlaskForm):
    """Parent form."""

    # It is an iterable in this case though
    # pylint: disable=not-an-iterable
    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(ViewForm, self).__init__(*args, **kwargs)

    num_buttons = generate_num_of_things_field('buttons')

    num_cams = generate_num_of_things_field('cameras')

    num_mail = generate_num_of_things_field('mail addresses')

    audio_bool = generate_audio_bool_field()

    visual_bool = generate_visual_bool_field()

    mail_bool = generate_mail_bool_field()

    slack_bool = generate_slack_bool_field()

    channel_name = generate_slack_channel_name_field()

    buttons = generate_buttons_field(ViewButtonForm)

    mails = generate_mails_field(MailForm)

    wbb_status, ble_status, inet_status = generate_status_fields()


class AdminForm(FlaskForm):
    """Parent form."""

    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    # Other
    error_log = StringField(
        Markup(_("Location of the error log") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _("Insert absolute path to the file. The default is /var/log/whiteboardbot/bot.log \
               but it&#39s recommended to not change this.") + "' " +
               INFO_ICON),
        validators=[validators.Regexp(r"^\/?([A-z0-9-_+]+\/)*([A-z0-9]+\.(log))$",
                                      message=_("Invalid path"))],
        render_kw={"placeholder": "/var/log/whiteboardbot/bot.log"}

    )

    sounds_dir = StringField(
        Markup(_("Location of sound directory") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('Absolute path to the sound folder') + "' " +
               INFO_ICON),
        validators=[validators.Regexp(r"\/[a-zA-Z0-9_\/-]*[^\/]$",
                                      message=_("Invalid path"))],
        render_kw={"placeholder": "/usr/lib/whiteboardbot/sounds"}

    )

    num_buttons = generate_num_of_things_field('buttons')

    num_cams = generate_num_of_things_field('cameras')

    num_mail = generate_num_of_things_field('mail addresses')

    audio_bool = generate_audio_bool_field()

    visual_bool = generate_visual_bool_field()

    mail_bool = generate_mail_bool_field()

    slack_bool = generate_slack_bool_field()

    fix_dist_bool = BooleanField(
        Markup(_("Use lens correction") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + ('Every camera lens has a distortion that warps images. \
               Correct this through setting distortion parameters for each camera. \
               Get these parameters through using a tool like &#39Hugin&#39 to \
               find out your camera&#39s lens parameters.') + "' " +
               INFO_ICON),
    )

    crop_bool = BooleanField(
        Markup(_("Crop image") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('Crop the image. \
                             Mostly used to get rid of black borders caused by fixing the lens distortion') + "' " +
               INFO_ICON),
    )

    enhance_bool = BooleanField(
        Markup(_("Enhance image") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _(
                   'Automatically enhances whiteboard images to be more legible and sends them additionally') + "' " +
               INFO_ICON),
    )

    token = StringField(
        Markup(_("Slack channel ")),
        render_kw={
            "placeholder": "xoxb-123456789012-123456789012-qgvqreiDsjgR4s7F7R0uShtr"}
    )

    request_bool = BooleanField(
        Markup(_("Activate request feature ") +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('Write !snap in your whiteboard channel, get the next image directly via DM') + "' " +
               INFO_ICON),
    )

    channel_name = generate_slack_channel_name_field()

    request_period = StringField(
        Markup(_("Request duration ")),
        render_kw={"placeholder": "60.0"}

    )

    trigger_sound, request_sound, error_sound, upload_sound, camera_sound, ready_sound = generate_sound_fields()

    address = StringField(
        Markup(_("E-Mail address of bot ")),
        render_kw={"placeholder": _("whiteboardbot@example.com")}
    )

    # NOTE: Saved in plaintext
    bot_password = StringField(
        Markup(_("Password of bot e-mail account") + " " +
               "<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' data-toggle='tooltip' " +
               "title='" + _('The password of the bot e-mail account') + "' " +
               INFO_ICON),
        render_kw={"placeholder": _("Hopefully not password1234")}
    )

    smtp = StringField(
        Markup(_("SMTP server of bot e-mail account ")),
        render_kw={"placeholder": _("mail.example.com")}
    )

    port = StringField(
        Markup(_("SMTP server port ")),
        render_kw={"placeholder": "465"}
    )

    buttons = generate_buttons_field(ButtonForm)

    cams = FieldList(
        FormField(CamForm, label=_("Camera")),
        min_entries=1
    )

    mails = generate_mails_field(MailForm)

    users = FieldList(
        FormField(UserForm, label=_("User")),
        min_entries=0
    )

    wbb_status, ble_status, inet_status = generate_status_fields()

    success = HiddenField(
        _('Saving status')
    )

    current_user = HiddenField(
        _('Name of current user')
    )

    submit = SubmitField(_('Submit'))

    def validate_request_period(self, field):
        """ Validate if request period is float"""
        slack_check = self.slack_bool.data
        request_check = self.request_bool.data
        if slack_check and request_check:
            pattern = re.compile(r"^[+-]?([0-9]*[.])?[0-9]+$")
            if pattern.match(str(field.data)) is None:
                raise ValidationError(
                    _('Invalid request period (must be decimal number)'))

    def validate_port(self, field):
        """ Validate if port number is valid"""
        mail_check = self.mail_bool.data
        if mail_check:
            pattern = re.compile(r"^((6553[0-5])|(655[0-2][0-9])|(65[0-4][0-9]{2})|"
                                 "(6[0-4][0-9]{3})|([1-5][0-9]{4})|([0-5]{0,5})|([0-9]{1,4}))$")
            if pattern.match(str(field.data)) is None:
                raise ValidationError(_('Invalid port number (usually 465, \
                        must be integer between 0 and 65535)'))

    def validate_smtp(self, field):
        """ Validate if SMTP address is valid"""
        mail_check = self.mail_bool.data
        if mail_check:
            pattern = re.compile(r"^((([A-Za-z0-9.-]+\."
                                 r"[A-Za-z0-9.-]+)+)|([A-Za-z0-9.-]+)).(([A-Za-z0-9.-]+\."
                                 r")+)([A-Za-z]{1,3})$")
            if pattern.match(str(field.data)) is None:
                raise ValidationError(_('Invalid SMTP address (e.g. mail.example.com)'))

    def validate_address(self, field):
        """ Validate if bot mail address is valid"""
        mail_check = self.mail_bool.data
        if mail_check:
            pattern = re.compile(
                r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
            if pattern.match(str(field.data)) is None:
                raise ValidationError(_('Invalid email address'))

    def validate_num_mail(self, field):
        """ Validate if number of mail is valid"""
        mail_check = self.mail_bool.data
        if mail_check:
            pattern = re.compile(r"^\b([0-9]|[1-3][0-9])\b$")
            if pattern.match(str(field.data)) is None:
                raise ValidationError(
                    _('Invalid number (Must be between 0 and 40)'))

    def validate_channel_name(self, field):
        """ Validate if Slack channel name is valid"""
        slack_check = self.slack_bool.data
        if slack_check:
            pattern = re.compile(r"^([a-z0-9_-]|#)[a-z0-9_-]{0,78}([a-z0-9])$")
            if pattern.match(field.data) is None:
                raise ValidationError(_('Invalid Slack channel name'))

    def validate_token(self, field):
        """ Validate if Slack token name is valid"""
        slack_check = self.slack_bool.data
        if slack_check:
            pattern = re.compile(r"^xox.-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}$")
            if pattern.match(field.data) is None:
                raise ValidationError(_('Invalid token. There must be a typo or \
                        copied the wrong token. It&#39s the &#39Bot User OAuth Access Token&#39'))

    def validate_cams(self, field):
        """ Validate if camera configs are valid"""
        dist_check = self.fix_dist_bool.data
        crop_check = self.crop_bool.data
        num_check = self.num_cams.data
        if isinstance(num_check, int):
            activated_fields = range(len(field))
            pattern = re.compile(r"^[0-9]+x[0-9]+$")
            used_sources = []
            for i in activated_fields:
                if num_check > i:
                    # Does the resolution have the right format?
                    if pattern.match(field[i].data['resolution']) is None:
                        field.errors.append({'resolution': [_('Resolution should be of format \
                                NUMBERxNUMBER e.g. 1920x1080')]})
                    # Is the source already in use?
                    if field[i].data['src'] in used_sources:
                        field.errors.append({'src': [_('Duplicate camera source detected. \
                                Change sources or delete cameras.')]})
                    else:
                        used_sources.append(field[i].data['src'])

            # Is distortion activated?
            if dist_check:
                pattern = re.compile(r"^([-+]?[0-9]+\.[0-9]+\s?){3,4}$")
                for i in activated_fields:
                    # Are the distortion metrics correct?
                    if num_check > i and (pattern.match(field[i].data['distMetrics']) is None):
                        field.errors.append({'distMetrics': [_('Parameters should be decimal \
                                numbers A B C [D] (D is optional) e.g. -0.0145 0.0 0.07')]})
            # Is cropping activated?
            if crop_check:
                pattern = re.compile(
                    r"^[0-9]+x[0-9]+([-+]?[0-9]+)?([-+]?[0-9]+)?$")
                for i in activated_fields:
                    # Are the crop metrics correct?
                    if num_check > i and (pattern.match(field[i].data['cropMetrics']) is None):
                        field.errors.append({'cropMetrics': [_('Parameters should be of format \
                                NUMBERxNUMBER[+/-]NUMBER[]+/-]NUMBER e.g. 4096x2160-20-40 or 4096x2160-0+40 or \
                                1920x1080")')]})

    def validate_buttons(self, field):
        """ Validate if button configs are valid"""
        num_check = self.num_buttons.data
        if isinstance(num_check, int):
            activated_fields = range(len(field))
            pattern = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
            used_macs = []
            for i in activated_fields:
                if num_check > i:
                    if pattern.match(field[i].data['mac']) is None:
                        field.errors.append({'mac': [_('Enter a valid MAC-Address \
                                e.g. ab:12:cd:34:ef:56')]})
                    if field[i].data['mac'] in used_macs:
                        field.errors.append({'mac': [_('Duplicate MAC-address detected. \
                         Edit MAC-addresses or delete a button')]})
                    else:
                        used_macs.append(field[i].data['mac'])


class LimitedForm(FlaskForm):
    """Parent form."""

    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(LimitedForm, self).__init__(*args, **kwargs)

    num_buttons = generate_num_of_things_field('buttons')

    num_cams = generate_num_of_things_field('cameras')

    num_mail = generate_num_of_things_field('mail addresses')

    audio_bool = generate_audio_bool_field()

    visual_bool = generate_visual_bool_field()

    mail_bool = generate_mail_bool_field()

    slack_bool = generate_slack_bool_field()

    channel_name = generate_slack_channel_name_field()

    buttons = generate_buttons_field(LimitedButtonForm)

    mails = generate_mails_field(MailForm)

    wbb_status, ble_status, inet_status = generate_status_fields()

    current_user = HiddenField(
        _('Name of current user')
    )

    success = HiddenField(
        _('Saving status')
    )
    submit = SubmitField(_('Submit'))

    def validate_num_mail(self, field):
        """ Validate if number of mail is valid"""
        mail_check = self.mail_bool.data
        if mail_check:
            pattern = re.compile(r"^\b([0-9]|[1-3][0-9])\b$")
            if pattern.match(str(field.data)) is None:
                raise ValidationError(
                    _('Invalid number (Must be less than 40)'))

    def validate_channel_name(self, field):
        """ Validate if Slack channel name is valid"""
        slack_check = self.slack_bool.data
        if slack_check:
            pattern = re.compile(r"^([a-z0-9_-]|#)[a-z0-9_-]{0,78}([a-z0-9])$")
            if pattern.match(field.data) is None:
                raise ValidationError(_('Invalid Slack channel name'))

    def validate_buttons(self, field):
        """ Validate if button configs are valid"""
        num_check = self.num_buttons.data
        if isinstance(num_check, int):
            activated_fields = range(len(field))
            pattern = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
            used_macs = []
            for i in activated_fields:
                if num_check > i:
                    if pattern.match(field[i].data['mac']):
                        used_macs.append(field[i].data['mac'])


class NewUserForm(FlaskForm):
    """ Form for adding a new user"""

    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(NewUserForm, self).__init__(*args, **kwargs)

    password, password_check = generate_password_fields()

    username = StringField(
        _('Username'),
        render_kw={"placeholder": _("Username of new user")}
    )
    success = HiddenField(
        _('Saving status')
    )
    submit = SubmitField(_('Submit'))

    def validate_username(self, field):
        """ Check if this is a proper username"""
        pattern = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")
        if 3 > len(field.data) > 32:
            raise ValidationError(
                _('Username should be between 3 and 32 characters.'))
        if pattern.match(field.data) is None:
            raise ValidationError(
                _('Only letters, numbers, "-" and "_" are allowed.'))
        users = dict(wbconf.get_section("Users"))
        roles = dict(wbconf.get_section("Roles"))
        if field.data in users or field.data in roles:
            raise ValidationError(_('This user already exists'))


class PasswordForm(FlaskForm):
    """ Form for changing passwords"""

    # Doesn't work for some reason
    # pylint: disable=super-with-arguments
    def __init__(self, *args, **kwargs):
        super(PasswordForm, self).__init__(*args, **kwargs)

    password, password_check = generate_password_fields()

    username = HiddenField(
        _('Username')
    )
    success = HiddenField(
        _('Saving status')
    )
    submit = SubmitField(_('Submit'))
