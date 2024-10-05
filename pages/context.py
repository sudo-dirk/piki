import inspect
import logging

from django.utils.translation import gettext as _


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
HELP_UID = 'help'


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
    add_back_menu(request, bar)
    # TODO: Add the pages navigation, if source is pages
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


def menubar(context, request, caller_name, **kwargs):
    bar = context[context.MENUBAR]
    # replace_profile(request, bar)
    add_help_menu(request, bar)
    # add_tasklist_menu(request, bar)
    # add_filter_submenu(request, bar, VIEW_TASKLIST_UID)
    # add_projectlist_menu(request, bar)
    # add_printview_menu(request, bar)
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
    if caller_name == 'pages':
        #    acc = acc_task(kwargs['task'], request.user)
        #    if acc.modify or acc.modify_limited:
        #        add_edittask_menu(request, bar, kwargs['task'].id)
        #    if acc.add_comments:
        #        add_newcomment_menu(request, bar, kwargs['task'].id)
        add_manageupload_menu(request, bar, kwargs['upload_path'])
    elif caller_name == 'helpview':
        actionbar_add_help(context, request, **kwargs)
    finalise_bar(request, bar)


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


"""from .access import create_project_possible, create_task_possible, acc_task
from django.db.models.functions import Lower
import patt
from .search import common_searches
from themes import empty_entry_parameters, color_icon_url, gray_icon_url
from users.context import PROFILE_ENTRY_UID


COMMENTNEW_UID = 'commentnew'
CREATE_PROJECT_UID = 'create-project'
CREATE_TASK_UID = 'create-task'
PRINTVIEW_UID = 'printview'
TASKEDIT_UID = 'taskedit'
VIEW_PROJECTLIST_UID = 'view-projectlist'
VIEW_TASKLIST_UID = 'view-tasklist'








def replace_profile(request, bar):
    try:
        bar.replace_entry(
            PROFILE_ENTRY_UID,
            PROFILE_ENTRY_UID,                          # uid
            request.user.username,                      # name
            color_icon_url(request, 'user.png'),        # icon
            patt.url_profile(request),                  # url
            False,                                      # left
            False                                       # active
        )
    except ValueError:
        pass        # Profile entry does not exist, so exchange is not needed (e.g. no user is logged in)




def add_tasklist_menu(request, bar):
    bar.append_entry(
        VIEW_TASKLIST_UID,                          # uid
        _('Tasklist'),                              # name
        color_icon_url(request, 'task.png'),        # icon
        patt.url_tasklist(request),                 # url
        True,                                       # left
        patt.is_tasklistview(request)               # active
    )


def add_projectlist_menu(request, bar):
    bar.append_entry(
        VIEW_PROJECTLIST_UID,                       # uid
        _('Projectlist'),                           # name
        color_icon_url(request, 'folder.png'),      # icon
        patt.url_projectlist(request),              # url
        True,                                       # left
        patt.is_projectlistview(request)            # active
    )


def add_printview_menu(request, bar):
    bar.append_entry(
        PRINTVIEW_UID,                              # uid
        _('Printview'),                             # name
        color_icon_url(request, 'print.png'),       # icon
        patt.url_printview(request),                # url
        True,                                       # left
        patt.is_printview(request)                  # active
    )


def add_newtask_menu(request, bar, project_id):
    bar.append_entry(
        CREATE_TASK_UID,                            # uid
        _('New Task'),                              # name
        color_icon_url(request, 'plus.png'),        # icon
        patt.url_tasknew(request, project_id),      # url
        True,                                       # left
        False                                       # active
    )


def add_edittask_menu(request, bar, task_id):
    bar.append_entry(
        TASKEDIT_UID,                               # uid
        _('Edit'),                                  # name
        color_icon_url(request, 'edit.png'),        # icon
        patt.url_taskedit(request, task_id),        # url
        True,                                       # left
        False                                       # active
    )


def add_newcomment_menu(request, bar, task_id):
    bar.append_entry(
        COMMENTNEW_UID,                             # uid
        _('Add Comment'),                           # name
        color_icon_url(request, 'edit2.png'),       # icon
        patt.url_commentnew(request, task_id),      # url
        True,                                       # left
        False                                       # active
    )


def add_newproject_menu(request, bar):
    bar.append_entry(
        CREATE_PROJECT_UID,                         # uid
        _('New Project'),                           # name
        color_icon_url(request, 'plus.png'),        # icon
        patt.url_projectnew(request),               # url
        True,                                       # left
        False                                       # active
    )






def add_filter_submenu(request, bar, menu_uid):
    bar.append_entry_to_entry(
        menu_uid,
        menu_uid + '-easysearch',             # uid
        _('Easysearch'),                        # name
        gray_icon_url(request, 'search.png'),   # icon
        patt.url_easysearch(request),           # url
        True,                                   # left
        False                                   # active
    )
    if patt.get_search_query(request) is not None:
        bar.append_entry_to_entry(
            menu_uid,
            menu_uid + '-save',                     # uid
            _('Save Search as Filter'),             # name
            gray_icon_url(request, 'save.png'),     # icon
            patt.url_filteredit(request),           # url
            True,                                   # left
            False                                   # active
        )
    bar.append_entry_to_entry(
        menu_uid,
        menu_uid + '-all',                      # uid
        _('All Tasks'),                         # name
        gray_icon_url(request, 'task.png'),     # icon
        patt.url_tasklist(request),             # url
        True,                                   # left
        False                                   # active
    )
    cs = common_searches(request)
    for common_filter_id in cs:
        bar.append_entry_to_entry(
            menu_uid,
            menu_uid + '-common',                                           # uid
            _(cs[common_filter_id][0]),                                     # name
            gray_icon_url(request, 'filter.png'),                           # icon
            patt.url_tasklist(request, common_filter_id=common_filter_id),  # url
            True,                                                           # left
            False                                                           # active
        )
    for s in request.user.search_set.order_by(Lower('name')):
        active = patt.is_tasklistview(request, s.id)
        if active is True:
            url = patt.url_filteredit(request, s.id)
        else:
            url = patt.url_tasklist(request, user_filter_id=s.id)
        if active:
            icon = 'settings.png'
        else:
            icon = 'favourite.png'
        bar.append_entry_to_entry(
            menu_uid,
            menu_uid + '-sub',              # uid
            s.name,                         # name
            gray_icon_url(request, icon),   # icon
            url,                            # url
            True,                           # left
            active                          # active
        )
"""
