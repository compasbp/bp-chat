import os, sys
from os.path import join, expanduser

APP_TITLE = 'BP Chat'
APP_NAME_LOWER = 'bp-chat'
APP_NAME_DIR = 'bp_chat'


def get_to_app_dir_path():
    LOCALAPPDATA = os.getenv('LOCALAPPDATA')
    app_path = LOCALAPPDATA + "/" + APP_NAME_DIR
    return app_path

def get_app_dir_path_with_uuid_suf(app_name=APP_NAME_LOWER, app_binary_path_type=False):
    path = get_app_dir_path(app_name, app_binary_path_type)
    suf = with_uid_suf('.chat')
    if suf:
        return join(path, suf)
    return path

def get_app_dir_path(app_name=APP_NAME_LOWER, app_binary_path_type=False):
    if is_win():
        if app_binary_path_type:
            appdata = os.getenv('LOCALAPPDATA')
        else:
            appdata = os.getenv('APPDATA')
        return join(appdata, app_name)
    else:
        return join(get_home_path(), "." + app_name)

def get_home_path():
    return expanduser("~")

def is_win():
    return sys.platform.startswith('win')


def with_uid_suf(uuid):
    for a in sys.argv:
        if a.startswith("UID_SUF="):
            return uuid + "_" + a[len("UID_SUF="):]
    return uuid
