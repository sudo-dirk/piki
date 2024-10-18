from django.conf import settings
from django.contrib import messages as django_messages
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext as _

import logging

from . import access
from . import messages
from . import url_page
from . import get_search_query
import config
from .context import context_adaption
from .forms import EditForm, RenameForm
from .help import help_pages
import mycreole
from .page import page_wrapped, page_list
from .search import whoosh_search, load_index, delete_item, add_item
from themes import Context

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


def root(request):
    return HttpResponseRedirect(url_page(config.STARTPAGE))


def page(request, rel_path):
    context = Context(request)      # needs to be executed first because of time mesurement
    #
    meta = "meta" in request.GET
    history = request.GET.get("history")
    if history:
        history = int(history)
    #
    p = page_wrapped(request, rel_path, history_version=history)
    if access.read_page(request, rel_path):
        if meta:
            page_content = p.render_meta()
        else:
            page_content = p.render_to_html()
        if history:
            messages.history_version_display(request, rel_path, history)
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
        page_content=page_content,
        is_available=p.userpage_is_available()
    )
    return render(request, 'pages/page.html', context=context)


def edit(request, rel_path):
    if access.write_page(request, rel_path):
        context = Context(request)      # needs to be executed first because of time mesurement
        #
        if not request.POST:
            history = request.GET.get("history")
            if history:
                history = int(history)
            #
            p = page_wrapped(request, rel_path, history_version=history)
            #
            form = EditForm(page_data=p.raw_page_src, page_tags=p.tags)
            #
            context_adaption(
                context,
                request,
                rel_path=rel_path,
                is_available=p.userpage_is_available(),
                form=form,
                # TODO: Add translation
                title=_("Edit page %s") % repr(p.title),
                upload_path=p.attachment_path,
            )
            return render(request, 'pages/page_edit.html', context=context)
        else:
            p = page_wrapped(request, rel_path)
            #
            save = request.POST.get("save")
            page_txt = request.POST.get("page_txt")
            tags = request.POST.get("page_tags")
            preview = request.POST.get("preview")
            #
            if save is not None:
                if p.update_page(page_txt, tags):
                    messages.edit_success(request)
                else:
                    messages.no_change(request)
                return HttpResponseRedirect(url_page(rel_path))
            elif preview is not None:
                form = EditForm(page_data=page_txt, page_tags=tags)
                #
                context_adaption(
                    context,
                    request,
                    rel_path=rel_path,
                    is_available=p.userpage_is_available(),
                    form=form,
                    # TODO: Add translation
                    title=_("Edit page %s") % repr(p.title),
                    upload_path=p.attachment_path,
                    page_content=p.render_text(request, page_txt)
                )
                return render(request, 'pages/page_edit.html', context=context)
            else:
                return HttpResponseRedirect(url_page(rel_path))
    else:
        messages.permission_denied_msg_page(request, rel_path)
        return HttpResponseRedirect(url_page(rel_path))


def delete(request, rel_path):
    if access.write_page(request, rel_path):
        context = Context(request)      # needs to be executed first because of time mesurement
        #
        if not request.POST:
            p = page_wrapped(request, rel_path)
            #
            # form = DeleteForm(page_data=p.raw_page_src, page_tags=p.tags)
            #
            context_adaption(
                context,
                request,
                rel_path=rel_path,
                is_available=p.userpage_is_available(),
                # form=form,
                # TODO: Add translation
                title=_("Delete page %s") % repr(p.title),
                upload_path=p.attachment_path,
                page_content=p.render_to_html(),
            )
        else:
            p = page_wrapped(request, rel_path)
            #
            delete = request.POST.get("delete")
            #
            if delete:
                # delete page from search index
                ix = load_index()
                delete_item(ix, p)
                # delete move files to history
                p.delete()
                # add delete message
                messages.page_deleted(request, p.title)
                return HttpResponseRedirect("/")
            else:
                messages.operation_canceled(request)
            return HttpResponseRedirect(url_page(rel_path))
        return render(request, 'pages/page_delete.html', context=context)
    else:
        messages.permission_denied_msg_page(request, rel_path)
        return HttpResponseRedirect(url_page(rel_path))


def rename(request, rel_path):
    if access.write_page(request, rel_path):
        context = Context(request)      # needs to be executed first because of time mesurement
        #
        if not request.POST:
            p = page_wrapped(request, rel_path)
            #
            form = RenameForm(page_name=p.rel_path)
            #
            context_adaption(
                context,
                request,
                rel_path=rel_path,
                is_available=p.userpage_is_available(),
                form=form,
                # TODO: Add translation
                title=_("Delete page %s") % repr(p.title),
                upload_path=p.attachment_path,
                page_content=p.render_to_html(),
            )
        else:
            p = page_wrapped(request, rel_path)
            #
            rename = request.POST.get("rename")
            page_name = request.POST.get("page_name")
            if rename:
                if page_name == p.rel_path:
                    messages.no_change(request)
                else:
                    # delete page from search index
                    ix = load_index()
                    delete_item(ix, p)
                    # rename the storage folder
                    p.rename(page_name)
                    # add the renamed page to the search index
                    add_item(ix, p)
                    # add rename message
                    messages.page_renamed(request)
            else:
                messages.operation_canceled(request)
            return HttpResponseRedirect(url_page(p.rel_path))
        return render(request, 'pages/page_rename.html', context=context)
    else:
        messages.permission_denied_msg_page(request, rel_path)
        return HttpResponseRedirect(url_page(rel_path))


def search(request):
    context = Context(request)      # needs to be executed first because of time mesurement
    #
    search_txt = get_search_query(request)

    sr = whoosh_search(search_txt)
    if sr is None:
        django_messages.error(request, _('Invalid search pattern: %s') % repr(search_txt))
        sr = []
    pl = page_list(request, [page_wrapped(request, rel_path) for rel_path in set(sr)])
    #
    context_adaption(
        context,
        request,
        title=_("Searchresults"),
        page_content=mycreole.render_simple(pl.creole_list())
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
