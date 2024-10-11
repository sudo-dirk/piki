from django.contrib import messages
from django.utils.translation import gettext as _
import pages


def permission_denied_msg_page(request, rel_path):
    # TODO: Add translation for this message
    messages.error(request, _("Permission denied: You don't have sufficient acces to the Page '%s'. Please contact the adminstrator.") % rel_path)


def unavailable_msg_page(request, rel_path):
    # TODO: Add translation for this message
    messages.info(request, _("Unavailable: The Page '%s' is not available. Create it or follow a valid link, please.") % rel_path)


def edit_success(request):
    # TODO: Add translation for this message
    messages.success(request, _('Thanks for editing, page stored.'))


def edit_no_change(request):
    # TODO: Add translation for this message
    messages.info(request, _("Nothing changed, no storage needed."))


def history_version_display(request, rel_path, history_version):
    # TODO: Add translation for this message
    messages.warning(request, _("You see an old version of the page (Version = %d). Click <a href='%s'>here</a> to recover this Version.") % (
        history_version,
        pages.url_edit(request, rel_path, history=history_version)
    ))
