import inspect
import logging
import os

from django.conf import settings
from django.utils.translation import gettext as _

from pages import access
import pages.parameter
from .help import actionbar as actionbar_add_help
import mycreole
import pages
from themes import empty_entry_parameters, gray_icon_url, color_icon_url
from users.context import menubar as menubar_users

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)

ATTACHMENT_UID = 'attachment'
BACK_UID = 'back'
EDIT_UID = 'edit'
HELP_UID = 'help'
INDEX_UID = 'index'
TREE_UID = 'tree'
NAVIGATION_ENTRY_UID = 'navigation-%s'


def cms_mode_active(request):
    user_logged_in = request.user.is_authenticated
    return pages.parameter.get(pages.parameter.CMS_MODE) and not user_logged_in


def context_adaption(context, request, **kwargs):
    caller_name = inspect.currentframe().f_back.f_code.co_name
    try:
        context.set_additional_title(kwargs.pop('title'))
    except KeyError:
        pass    # no title in kwargs
    menubar(context, request, caller_name, **kwargs)
    actionbar(context, request, caller_name, **kwargs)
    navigationbar(context, request, caller_name, **kwargs)
    for key in kwargs:
        context[key] = kwargs[key]
    logger.debug("context adapted: %s", repr(context))


def navigationbar(context, request, caller_name, **kwargs):
    bar = context[context.NAVIGATIONBAR]
    if caller_name == "mycreole-attachments":
        next = kwargs.get("next")
        if next.count("/") >= 2:
            path = next[next.find("/", 2) + 1:]
        else:
            path = ""
    else:
        path = kwargs.get("rel_path", "")
    while len(path) > 0 and path != os.path.sep:
        bar.append_entry(*navigation_entry_parameters(request, path))
        path = os.path.dirname(path)
    bar.append_entry(*empty_entry_parameters(request))
    add_back_menu(request, bar)
    finalise_bar(request, bar)


def menubar(context, request, caller_name, **kwargs):
    bar = context[context.MENUBAR]
    if not cms_mode_active(request):
        menubar_users(bar, request)
        add_help_menu(request, bar, "current_help_page" in kwargs)
    add_nav_links(request, bar, kwargs.get("rel_path", ''))
    finalise_bar(request, bar)


def actionbar(context, request, caller_name, **kwargs):
    bar = context[context.ACTIONBAR]
    if not cms_mode_active(request):
        if caller_name in ['page', 'edit', 'delete', 'rename']:
            if access.write_page(request, kwargs["rel_path"]):
                add_page_menu(request, bar, kwargs["rel_path"], kwargs.get('is_available', False))
            if access.modify_attachment(request, kwargs["rel_path"]):
                add_manageupload_menu(request, bar, kwargs['upload_path'], kwargs.get('is_available', False))
            if access.read_page(request, kwargs["rel_path"]):
                add_meta_menu(request, bar, kwargs["rel_path"], kwargs.get('is_available', False))
        elif caller_name == 'helpview':
            actionbar_add_help(context, request, **kwargs)
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
        pages.url_page(path),                                   # url
        False,                                                  # left
        False                                                   # active
    )


def add_help_menu(request, bar, active):
    bar.append_entry(
        HELP_UID,                                   # uid
        _('Help'),                                  # name
        color_icon_url(request, 'help.png'),        # icon
        pages.url_helpview('main'),                 # url
        True,                                       # left
        active                                      # active
    )


def add_nav_links(request, bar, rel_path):
    bar.append_entry(
        INDEX_UID,                                  # uid
        _('Index'),                                 # name
        color_icon_url(request, 'edit.png'),        # icon
        pages.url_page('index'),                    # url
        True,                                       # left
        request.path == "/page/index"               # active
    )
    bar.append_entry(
        TREE_UID,                                   # uid
        _('Tree'),                                  # name
        color_icon_url(request, 'tree.png'),        # icon
        pages.url_page('tree'),                     # url
        True,                                       # left
        request.path == "/page/tree"                # active
    )


def add_page_menu(request, bar, rel_path, is_available):
    bar.append_entry(
        EDIT_UID,                                   # uid
        _('Edit'),                                  # name
        color_icon_url(request, 'edit2.png'),       # icon
        pages.url_edit(rel_path),                   # url
        True,                                       # left
        request.path == pages.url_edit(rel_path)    # active
    )
    if is_available:
        bar.append_entry(
            EDIT_UID,                                   # uid
            _('Rename'),                                # name
            color_icon_url(request, 'shuffle.png'),     # icon
            pages.url_rename(rel_path),                 # url
            True,                                       # left
            request.path == pages.url_rename(rel_path)  # active
        )
        bar.append_entry(
            EDIT_UID,                                   # uid
            _('Delete'),                                # name
            color_icon_url(request, 'delete.png'),      # icon
            pages.url_delete(rel_path),                 # url
            True,                                       # left
            request.path == pages.url_delete(rel_path)  # active
        )


def add_manageupload_menu(request, bar, upload_path, is_available):
    if is_available:
        bar.append_entry(
            ATTACHMENT_UID,                                                     # uid
            _("Attachments"),                                                   # name
            color_icon_url(request, 'upload.png'),                              # icon
            mycreole.url_manage_uploads(request, upload_path),                  # url
            True,                                                               # left
            False,                                                              # active
        )


def add_meta_menu(request, bar, rel_path, is_available):
    if is_available:
        if "meta" in request.GET:
            bar.append_entry(
                EDIT_UID,                                       # uid
                _('Page'),                                      # name
                color_icon_url(request, 'display.png'),         # icon
                pages.url_page(rel_path),                       # url
                True,                                           # left
                False                                           # active
            )
        else:
            bar.append_entry(
                EDIT_UID,                                       # uid
                _('Meta'),                                      # name
                color_icon_url(request, 'info.png'),            # icon
                pages.url_page(rel_path, meta=None),            # url
                True,                                           # left
                False                                           # active
            )


def finalise_bar(request, bar):
    if len(bar) == 0:
        bar.append_entry(*empty_entry_parameters(request))
