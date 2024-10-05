from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext as _

import logging

from . import access
from . import messages
from . import url_page
import config
from .context import context_adaption
from .forms import EditForm
from .help import help_pages
import mycreole
from .page import creol_page
from themes import Context

logger = logging.getLogger(__name__)


def root(request):
    return HttpResponseRedirect(url_page(request, config.STARTPAGE))


def page(request, rel_path):
    context = Context(request)      # needs to be executed first because of time mesurement
    #
    p = creol_page(rel_path)
    if access.read_page(request, rel_path):
        page_content = p.render_to_html(request)
    else:
        messages.permission_denied_msg_page(request, rel_path)
        page_content = ""
    #
    context_adaption(
        context,
        request,
        rel_path=rel_path,
        title=p.title,
        upload_path=p.attachment_path,
        page_content=page_content
    )
    return render(request, 'pages/page.html', context=context)


def edit(request, rel_path):
    if access.write_page(request, rel_path):
        context = Context(request)      # needs to be executed first because of time mesurement
        #
        p = creol_page(rel_path)
        #
        if not request.POST:
            form = EditForm(page_data=p.raw_page_src)
            #
            context_adaption(
                context,
                request,
                form=form,
                # TODO: Add translation
                title=_("Edit page %s") % repr(p.title),
                upload_path=p.attachment_path,
            )
            return render(request, 'pages/page_form.html', context=context)
        else:
            save = request.POST.get("save")
            page_txt = request.POST.get("page_txt")
            preview = request.POST.get("preview")
            #
            if save is not None:
                p.update_page(page_txt)
                return HttpResponseRedirect(url_page(request, rel_path))
            elif preview is not None:
                form = EditForm(page_data=page_txt)
                #
                context_adaption(
                    context,
                    request,
                    form=form,
                    # TODO: Add translation
                    title=_("Edit page %s") % repr(p.title),
                    upload_path=p.attachment_path,
                    page_content=mycreole.render(request, page_txt, p.attachment_path, 'next-anchor')
                )
                return render(request, 'pages/page_form.html', context=context)
            else:
                return HttpResponseRedirect(url_page(request, rel_path))
    else:
        messages.permission_denied_msg_page(request, rel_path)
        return HttpResponseRedirect(url_page(request, rel_path))


def search(request):
    context = Context(request)      # needs to be executed first because of time mesurement
    context_adaption(
        context,
        request,
        page_content="Search is not yet implemented..."
    )
    return render(request, 'pages/page.html', context=context)


def helpview(request, page='main'):
    context = Context(request)      # needs to be executed first because of time mesurement
    page_content = help_pages[page]
    context_adaption(
        context,                            # the base context
        request,                            # the request object to be used in context_adaption
        current_help_page=page,             # the current help_page to identify which taskbar entry has to be highlighted
        page_content=page_content,          # the help content itself (template)
        title=_('Help')                     # the title for the page (template)
    )
    return render(request, 'pages/page.html', context=context)
