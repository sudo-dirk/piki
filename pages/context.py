import inspect
import logging
import os

from django.utils.translation import gettext as _


from pages import access
from .help import actionbar as actionbar_add_help
import mycreole
import pages
from themes import empty_entry_parameters, gray_icon_url, color_icon_url
from users.context import menubar as menubar_users

try:
    from config import APP_NAME as ROOT_LOGGER_NAME
except ImportError:
    ROOT_LOGGER_NAME = 'root'
logger = logging.getLogger(ROOT_LOGGER_NAME).getChild(__name__)

ATTACHMENT_UID = 'attachment'
BACK_UID = 'back'
EDIT_UID = 'edit'
HELP_UID = 'help'
NAVIGATION_ENTRY_UID = 'navigation-%s'


def context_adaption(context, request, **kwargs):
    caller_name = inspect.currentframe().f_back.f_code.co_name
    try:
        context.set_additional_title(kwargs.pop('title'))
    except KeyError:
        pass    # no title in kwargs
    menubar_users(context[context.MENUBAR], request)
    menubar(context, request, caller_name, **kwargs)
    actionbar(context, request, caller_name, **kwargs)
    navigationbar(context, request, caller_name, **kwargs)
    for key in kwargs:
        context[key] = kwargs[key]
    logger.debug("context adapted: %s", repr(context))


def navigationbar(context, request, caller_name, **kwargs):
    bar = context[context.NAVIGATIONBAR]
    path = kwargs.get("rel_path", "")
    while len(path) > 0 and path != os.path.sep:
        bar.append_entry(*navigation_entry_parameters(request, path))
        path = os.path.dirname(path)
    add_back_menu(request, bar)
    finalise_bar(request, bar)


def add_back_menu(request, bar):
    bar.append_entry(
        BACK_UID,                                   # uid
        _('Back'),                                  # name
        gray_icon_url(request, 'back.png'),         # icon
        'javascript:history.back()',                # url
        True,                                       # left
        False                                       # active
    )


def navigation_entry_parameters(request, path):
    return (
        NAVIGATION_ENTRY_UID % os.path.basename(path),          # uid
        '/' + os.path.basename(path),                           # name
        None,                                                   # icon
        pages.url_page(request, path),                          # url
        False,                                                  # left
        False                                                   # active
    )


def menubar(context, request, caller_name, **kwargs):
    bar = context[context.MENUBAR]
    add_help_menu(request, bar)
    finalise_bar(request, bar)


def add_help_menu(request, bar):
    bar.append_entry(
        HELP_UID,                                   # uid
        _('Help'),                                  # name
        color_icon_url(request, 'help.png'),        # icon
        pages.url_helpview(request, 'main'),        # url
        True,                                       # left
        False                                       # active
    )


def actionbar(context, request, caller_name, **kwargs):
    bar = context[context.ACTIONBAR]
    if caller_name == 'page':
        if access.write_page(request, kwargs["rel_path"]):
            add_edit_menu(request, bar, kwargs["rel_path"])
        if access.modify_attachment(request, kwargs["rel_path"]):
            add_manageupload_menu(request, bar, kwargs['upload_path'])
    elif caller_name == 'helpview':
        actionbar_add_help(context, request, **kwargs)
    finalise_bar(request, bar)


def add_edit_menu(request, bar, rel_path):
    bar.append_entry(
        EDIT_UID,                                   # uid
        _('Edit'),                                  # name
        color_icon_url(request, 'edit.png'),        # icon
        pages.url_edit(request, rel_path),          # url
        True,                                       # left
        False                                       # active
    )


def add_manageupload_menu(request, bar, upload_path):
    bar.append_entry(
        ATTACHMENT_UID,                                                     # uid
        _("Attachments"),                                                   # name
        color_icon_url(request, 'upload.png'),                              # icon
        mycreole.url_manage_uploads(request, upload_path),                  # url
        True,                                                               # left
        False,                                                              # active
    )


def finalise_bar(request, bar):
    if len(bar) == 0:
        bar.append_entry(*empty_entry_parameters(request))
