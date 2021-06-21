"""
Backend for Config webserver

:Author: Andreas Lindlbauer (@alindl)
:Copyright: (c) 2021 University of Salzburg
:Organization: Center for Human-Computer Interaction
"""

__license__ = "GNU GPLv3"
__docformat__ = 'reStructuredText'

import json
import os
import subprocess
from collections import namedtuple
from datetime import datetime

from flask import Flask, render_template, send_from_directory, \
    request, session, g, redirect, url_for
from flask_babel import gettext as _, ngettext, Babel
from flask_bootstrap import Bootstrap
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import read_config as wbconf
from forms import AdminForm, LimitedForm, NewUserForm, PasswordForm, \
    ViewForm
import check_internet as wbci
from ble_interaction import ScanDelegate

# NOTE Security real talk:
#      We are saving the password for the bot mail account in plain text.
#      You have bigger issues to deal with, if somebody has access to the SoC that is running
#      this code as that SoC and account should only be accessible from the inside network.
#      Similar issue with the login for the edit page. This is not about security, it's about
#      making sure that users, that don't know any better don't accidentally change something,
#      or maliciously change stuff to be nosey.
#      This should NEVER be accessible from outside the network.

# Init Flask
app = Flask(__name__)
# NOTE key not really important, this isn't going to be online anyway
# TODO generate a secret key through setup script
# app.config['SECRET_KEY'] = 'keepthissecret'
app.config['SECRET_KEY'] = os.urandom(16)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
Bootstrap(app)
babel = Babel(app)

app.config['SUPPORTED_LANGUAGES'] = {'de': 'German', 'en': 'English', 'ja': 'Japanese'}
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

app.debug = True # TODO Don't forget to deactivate that

auth = HTTPBasicAuth()


@auth.get_user_roles
def get_user_roles(user):
    """ Get the role/permission level of this specific user """

    # This is for manual usage
    if isinstance(user, str):
        username = user
    # This is for Flask HTTPauth, as it uses a user object
    else:
        username = user.username

    # Get list of registered users
    users = dict(wbconf.get_section("Users"))

    # Check if the user even exists
    if username in users:
        # Get list of registered users
        roles = dict(wbconf.get_section("Roles"))

        # Check which roles a user has, if any
        if username in roles:
            return [roles.get(username)]

    # User not found
    return False


@auth.verify_password
def verify_password(username, password):
    """ Get the password hash from the config and compare it to input """
    # Get list of registered users
    users = dict(wbconf.get_section("Users"))
    # Check if this user exists and the password matches the password hash on file
    if username in users and check_password_hash(users.get(username), password):
        # Return username as confirmation
        return username
    return False


def generate_buttons(read_only_val):
    """ Generate button data for form """
    # Mirror the format of the button information from the config file
    button = namedtuple(
        'Button', ['mac', 'timevar', 'action', 'read_only', 'btn_name'])
    buttons = []
    btn_num = 0
    # Get the information for each button, embed them into the format and append to button list
    while wbconf.has_section("Button" + str(btn_num)):
        tmp_btn = wbconf.get_section('Button' + str(btn_num))
        buttons.append(button(tmp_btn[0][1], datetime.fromisoformat(tmp_btn[1][1]),
                              json.loads(tmp_btn[2][1].replace('\'', '"')),
                              read_only_val, tmp_btn[3][1]))
        btn_num += 1
    return buttons


def generate_cams(read_only_val):
    """ Generate cam data for form """
    # Mirror the format of the cam information from the config file
    cam = namedtuple('Camera', ['src', 'resolution',
                                'distMetrics', 'cropMetrics', 'read_only'])
    cams = []
    cm_num = 0
    # Get the information for each cam, embed them into the format and append to cam list
    while wbconf.has_section("Cam" + str(cm_num)):
        tmp_cm = wbconf.get_section('Cam' + str(cm_num))
        cams.append(cam(tmp_cm[0][1],
                        tmp_cm[1][1],
                        tmp_cm[2][1],
                        tmp_cm[3][1],
                        read_only_val))
        cm_num += 1
    return cams


def generate_mails(read_only_val):
    """ Generate mail data for form """
    # Mirror the format of the mail information from the config file
    mail = namedtuple('Mail', ['address', 'read_only'])
    mails = []
    ml_num = 0
    # Get the information for each mail, embed them into the format and append to mail list
    while wbconf.has_section("Mail" + str(ml_num)):
        tmp_ml = wbconf.get_section('Mail' + str(ml_num))
        mails.append(mail(tmp_ml[0][1], read_only_val))
        ml_num += 1
    return mails


def generate_users(read_only_val):
    """ Generate user data for form """
    # Mirror the format of the user information from the config file
    user = namedtuple('User', ['username', 'read_only'])
    users = []
    # Get the information for each user, embed them into the format and append to user list
    for name in dict(wbconf.get_section('Users')).keys():
        users.append(user(name, read_only_val))
    return users


def generate_data(choice, read_only_val):
    """ Generate input data for form """

    # Get state of whiteboardbot, bluetooth and internet connection
    # NOTE: We don't check because we need the error codes.
    # A check would make it unnecessarily complicated to deal with exit codes
    # pylint: disable=subprocess-run-check
    wbb_status = subprocess.run("systemctl is-active whiteboardbot.service".split(),
                                capture_output=True).stdout.decode("utf-8").rstrip()
    ble_status = subprocess.run("systemctl is-active bluetooth.service".split(),
                                capture_output=True).stdout.decode("utf-8").rstrip()
    inet_status = wbci.internet()

    # Get all data for forms
    data = {
        'error_log': wbconf.get_key('Other', 'error_log'),
        'sounds_dir': wbconf.get_key('Other', 'sounds_dir'),
        'num_buttons': wbconf.get_key('Output', 'num_buttons'),
        'num_cams': wbconf.get_key('Output', 'num_cameras'),
        'audio_bool': wbconf.get_bool_key('Output', 'audio'),
        'visual_bool': wbconf.get_bool_key('Output', 'visual'),
        'mail_bool': wbconf.get_bool_key('Output', 'mail'),
        'num_mail': wbconf.get_key('Output', 'num_mail'),
        'slack_bool': wbconf.get_bool_key('Output', 'slack'),
        'fix_dist_bool': wbconf.get_bool_key('Output', 'fix_distortion'),
        'crop_bool': wbconf.get_bool_key('Output', 'fix_crop'),
        'enhance_bool': wbconf.get_bool_key('Output', 'enhance'),
        'token': wbconf.get_key('Slack', 'token'),
        'request_bool': wbconf.get_bool_key('Slack', 'request'),
        'channel_name': wbconf.get_key('Slack', 'channel_name')[len("#"):],
        'request_period': wbconf.get_key('Slack', 'request_period'),
        'trigger_sound': wbconf.get_key('Sound_Sources', 'trigger'),
        'request_sound': wbconf.get_key('Sound_Sources', 'request'),
        'error_sound': wbconf.get_key('Sound_Sources', 'error'),
        'upload_sound': wbconf.get_key('Sound_Sources', 'upload'),
        'camera_sound': wbconf.get_key('Sound_Sources', 'camera'),
        'ready_sound': wbconf.get_key('Sound_Sources', 'ready'),
        'address': wbconf.get_key('Mail_Bot', 'address'),
        'bot_password': wbconf.get_key('Mail_Bot', 'bot_password'),
        'smtp': wbconf.get_key('Mail_Bot', 'SMTP'),
        'port': wbconf.get_key('Mail_Bot', 'port'),
        'buttons': generate_buttons(read_only_val) if 'button' in choice else '',
        'cams': generate_cams(read_only_val) if 'cam' in choice else '',
        'mails': generate_mails(read_only_val) if 'mail' in choice else '',
        'users': generate_users(read_only_val) if 'user' in choice else '',
        'current_user': auth.current_user(),
        'wbb_status': wbb_status,
        'ble_status': ble_status,
        'inet_status': inet_status,
        'read_only': read_only_val,
        'success': False

    }
    return data


@app.errorhandler(404)
def page_not_found(error):
    """ Render 404 Not Found page """
    return render_template('404.html'), error


@app.route("/error", methods=['GET'])
def credential_error_page(status):
    """ Render all other error pages """
    # Incorrect credentials => 401 Unauthorized
    if status == '401':
        return render_template('401.html'), 401
    # Correct, but insufficient permission => 403 Forbidden
    if status == '403':
        return render_template('403.html'), 403
    # Other error
    return render_template('error.html')


@app.route("/", methods=['GET', 'POST'])
def status_page():
    """ Render status page that shows most important information """
    config = wbconf.get_config()
    # Check a bunch of states that would indicate that there is no admin user
    if not config.has_section('Users') or \
            not config.has_section('Roles') or \
            not config.has_option("Users", "admin") or \
            not config.has_option("Roles", "admin") or \
            not config.get('Users', 'admin'):
        # Initialize the admin user
        return init_admin()

    # Render status page if admin is set up
    form = ViewForm(data=generate_data(['button', 'mail'], True))
    return render_template('index.html', form=form)


def admin_edit_page():
    """ Render admin edit page that allows the admin to change every setting """
    # Generate form for admin page
    form = AdminForm(data=generate_data(
        ['cam', 'button', 'mail', 'user'], False))

    # If any changes were submitted
    if form.validate_on_submit():

        # Get information from config file and update from form fields
        # NOTE: We could check if the values are the same, but does it really matter?
        # We have write the whole file anyway
        config = wbconf.get_config()
        config['Other'] = {
            'error_log': form.error_log.data,
            'sounds_dir': form.sounds_dir.data
        }
        config['Output'] = {
            'num_buttons': form.num_buttons.data,
            'num_cameras': form.num_cams.data,
            'audio': form.audio_bool.data,
            'visual': form.visual_bool.data,
            'slack': form.slack_bool.data,
            'fix_distortion ': form.fix_dist_bool.data,
            'fix_crop': form.crop_bool.data,
            'enhance': form.enhance_bool.data,
            'mail': form.mail_bool.data,
            'num_mail': form.num_mail.data
        }

        # Only write data from form if slack is even activated
        config['Slack'] = {
            'token': form.token.data,
            'request': form.request_bool.data,
            # Make sure that the channelname has the hash symbol in it
            'channel_name': ("#" + form.channel_name.data.strip("#")),
            # Only update request time if the request feature is activated
            'request_period': form.request_period.data
            if form.request_bool.data
            else wbconf.get_key('Slack', 'request_period')
        }

        # Only write data from sound sources if audio feedback is activated
        if form.audio_bool.data:
            config['Sound_Sources'] = {
                'trigger': form.trigger_sound.data,
                'request': form.request_sound.data,
                'error': form.error_sound.data,
                'upload': form.upload_sound.data,
                'camera': form.camera_sound.data,
                'ready': form.ready_sound.data
            }

        # Only write data for the mail bot if mail is even activated
        if form.mail_bool.data:
            config['Mail_Bot'] = {
                'address': form.address.data,
                'bot_password': form.bot_password.data,
                'SMTP': form.smtp.data,
                'port': form.port.data
            }

        # Loop through every activated camera
        for cm_num in range(0, form.num_cams.data):
            config['Cam' + str(cm_num)] = {
                'src': form.cams[cm_num]['src'].data,
                'resolution': form.cams[cm_num]['resolution'].data,
                'correction_metrics': form.cams[cm_num]['distMetrics'].data,
                'cropping_metrics': form.cams[cm_num]['cropMetrics'].data
            }

        set_buttons(form, config)
        set_mail_addresses(form, config)

        wbconf.write_config(config)
        # Flag that is needed for showing a successful write to the user
        form.success.data = True
    return render_template('admin.html', form=form)


def set_buttons(form, config):
    """ Set all buttons from form info if available"""

    # Loop through every activated button
    for btn_num in range(0, form.num_buttons.data):
        if not 'Button' + str(btn_num) in config:
            config['Button' + str(btn_num)] = {}
        for field_name in ['mac', 'timevar', 'action', 'btn_name']:
            if form.buttons[btn_num][field_name].data:
                config['Button' + str(btn_num)][field_name] = str(form.buttons[btn_num][field_name].data)

        # Update the available choices in the SelectMultipleField of the buttons
        form.buttons[btn_num]['action'].choices = get_choices(form)

    # Update list of mac addresses at the BLE scanner
    ScanDelegate.button_list = [dict(config.items('Button' + str(i))) for i in range(int(form.num_buttons.data))]


def get_choices(form):
    """ Fetch the updated list of available choices """
    choices = [('normal', _('Send to all activated outputs')), ('slack', _('Send to Slack')),
               ('all_mail', _('Send to all mail addresses'))]

    if form.mail_bool.data:
        for ml_num in range(0, int(form.num_mail.data) if int(form.num_mail.data) < 40 else 39):
            choices.append(("mail_" + str(ml_num), "Send to mail address: " +
                            form.mails[ml_num]['address'].data))
    return choices


def set_mail_addresses(form, config):
    """ Set all mail addresses from form if activated """
    if form.mail_bool.data:
        for ml_num in range(0, int(form.num_mail.data) if int(form.num_mail.data) < 40 else 39):
            config['Mail' + str(ml_num)] = {
                'address': form.mails[ml_num]['address'].data
            }


def limited_edit_page():
    """ Render a limited edit page that allows privileged users to change some settings """
    form = LimitedForm(data=generate_data(['cam', 'button', 'mail'], False))
    # if not form.slack_bool.data and not form.mail_bool.data:
    #    raise ValidationError('Some output must be activated. Either Mail or Slack.')
    if form.validate_on_submit():

        config = wbconf.get_config()
        if form.num_mail.data:
            config['Output']['num_mail'] = str(form.num_mail.data)
        else:
            config['Output']['num_mail'] = wbconf.get_key('Output', 'num_mail')

        if form.slack_bool.data:
            config['Slack']['channel_name'] = (
                    "#" + form.channel_name.data.strip("#"))
        else:
            config['Slack']['channel_name'] = wbconf.get_key(
                'Slack', 'channel_name')

        set_mail_addresses(form, config)
        set_buttons(form, config)

        wbconf.write_config(config)
        form.success.data = True
    return render_template('limited.html', form=form)


@app.route("/new_user", methods=['POST', 'GET'])
@auth.login_required(role=['admin'])
def add_new_user():
    """ Add a new user """
    form = NewUserForm()
    if form.validate_on_submit():

        if form.password.data and form.password_check.data and form.username.data:
            config = wbconf.get_config()
            config['Users'][form.username.data] = generate_password_hash(
                form.password.data)
            config['Roles'][form.username.data] = "limited"
            wbconf.write_config(config)
            form.success.data = True
            return redirect(url_for('config_page'))
    return render_template('new_user.html', form=form)


@app.route("/init_admin", methods=['POST', 'GET'])
def init_admin():
    """ Initialize the admin user """
    config = wbconf.get_config()
    if not config.has_section('Users'):
        config.add_section('Users')
        wbconf.write_config(config)

    if not config.has_section('Roles'):
        config.add_section('Roles')
        wbconf.write_config(config)

    if not config.has_option("Users", "admin") or \
            not config.has_option("Roles", "admin") or \
            not config.get('Users', 'admin'):
        form = PasswordForm(data={'username': 'admin'})
        if form.validate_on_submit():
            if form.password.data and form.password_check.data:
                config['Users']['admin'] = generate_password_hash(
                    form.password.data)
                config['Roles']['admin'] = 'admin'
                wbconf.write_config(config)
                form.success.data = True
                return redirect(url_for('status_page'))
        return render_template('change_password.html', form=form)
    return redirect(url_for('status_page'))


@app.route("/change_password/<username>", methods=['POST', 'GET'])
@auth.login_required(role=['admin', 'limited'])
def change_password(username):
    """ Change the password of user """
    if username == auth.current_user() or "admin" in get_user_roles(auth.current_user()):
        form = PasswordForm(data={'username': username})
        if form.validate_on_submit():

            config = wbconf.get_config()
            if form.password.data and form.password_check.data:
                config['Users'][username] = generate_password_hash(
                    form.password.data)
                wbconf.write_config(config)
                form.success.data = True
                return redirect(url_for('status_page'))
        return render_template('change_password.html', form=form)
    # Not allowed here
    return render_template('403.html'), 403


@app.route("/delete_user/<username>", methods=['POST', 'GET'])
@auth.login_required(role=['admin'])
def delete_user(username):
    """ Change the password of user """
    if username == "admin":
        return render_template('403.html'), 403
    if username == auth.current_user() or "admin" in get_user_roles(auth.current_user()):
        config = wbconf.get_config()
        config.remove_option('Users', username)
        config.remove_option('Roles', username)
        wbconf.write_config(config)
        return redirect(url_for('config_page'))
    # Not allowed here
    return render_template('403.html'), 403


@auth.error_handler
def handle_error(status):
    return credential_error_page(str(status))


@app.route("/edit", methods=['POST', 'GET'])
@auth.login_required(role=['admin', 'limited'])
def config_page():
    """ Just the config site """

    if 'admin' in get_user_roles(auth.current_user()):
        return admin_edit_page()

    if 'limited' in get_user_roles(auth.current_user()):
        return limited_edit_page()


@app.route('/favicon.ico')
def favicon():
    """ How to have a favicon """
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@babel.localeselector
def get_locale():
    if request.accept_languages[0][0][:2] in ("de", "en", "ja"):
        session['lang'] = request.accept_languages[0][0][:2]
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')


@babel.timezoneselector
def get_timezone():
    user = g.get('user', None)
    if user is not None:
        return user.timezone


@app.url_defaults
def set_language_code(endpoint, values):
    if 'lang_code' in values or not g.get('lang_code', None):
        return
    if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
        values['lang_code'] = g.lang_code


@app.url_value_preprocessor
def get_lang_code(endpoint, values):
    if values is not None:
        g.lang_code = values.pop('lang_code', None)


@app.before_request
def ensure_lang_support():
    lang_code = g.get('lang_code', None)
    if lang_code and lang_code not in app.config['SUPPORTED_LANGUAGES'].keys():
        return page_not_found(404)


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5002, debug=True)
