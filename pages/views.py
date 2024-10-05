from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext as _

import logging

import config
from . import url_page
from .context import context_adaption
from .help import help_pages
from .page import page
from themes import Context

logger = logging.getLogger(__name__)


def root(request):
    return HttpResponseRedirect(url_page(request, config.STARTPAGE))


def pages(request, rel_path=''):
    context = Context(request)      # needs to be executed first because of time mesurement
    #
    p = page(rel_path)
    #
    context_adaption(
        context,
        request,
        title=p.title,
        upload_path=p.attachment_path,
        page_content=p.render_to_html(request)
    )
    return render(request, 'pages/page.html', context=context)


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
