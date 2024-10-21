from django.conf import settings
from django.contrib import messages as django_messages
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext as _

import logging


from .access import access_control
from . import messages
from . import url_page
from . import get_search_query
import config
from .context import context_adaption
from .forms import EditForm, RenameForm
from .help import help_pages
from .models import PikiPage, page_list
import mycreole
from .search import whoosh_search, load_index, delete_item, add_item, update_item
from themes import Context

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


SUCCESS_PAGE = _("""= Default startpage
**Congratulations!!!**

Seeing this page means, that you installed Piki successfull.

Edit this page to get your own first startpage.

If you need need assistance to edit a page, visit the [[/helpview/main|help pages]].
""")


def root(request):
    return HttpResponseRedirect(url_page(config.STARTPAGE))


def page(request, rel_path):
    context = Context(request)      # needs to be executed first because of time mesurement
    #
    try:
        p = PikiPage.objects.get(rel_path=rel_path)
    except PikiPage.DoesNotExist:
        p = None
    meta = "meta" in request.GET
    history = request.GET.get("history")
    if history:
        history = int(history)
    #
    title = rel_path.split("/")[-1]
    #
    acc = access_control(request, rel_path)
    if acc.may_read():
        if p is None or p.deleted:
            if rel_path == config.STARTPAGE:
                page_content = mycreole.render_simple(SUCCESS_PAGE)
            else:
                page_content = ""
            if p is not None and p.deleted:
                messages.deleted_page(request)
            else:
                messages.unavailable_msg_page(request, rel_path)
        else:
            title = p.title
            if meta:
                page_content = p.render_meta(request, history)
            else:
                page_content = p.render_to_html(request, history)
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
        title=title,
        upload_path=rel_path,
        page_content=page_content,
        is_available=p is not None and not p.deleted
    )
    return render(request, 'pages/page.html', context=context)


def edit(request, rel_path):
    acc = access_control(request, rel_path)
    if acc.may_write():
        context = Context(request)      # needs to be executed first because of time mesurement
        #
        try:
            p = PikiPage.objects.get(rel_path=rel_path)
            is_available = True
        except PikiPage.DoesNotExist:
            p = PikiPage(rel_path=rel_path)
            is_available = False
        #
        if not request.POST:
            history = request.GET.get("history")
            if history:
                history = int(history)
                form = EditForm(instance=p.history.get(history_id=history))
            else:
                form = EditForm(instance=p)
            #
            context_adaption(
                context,
                request,
                rel_path=rel_path,
                is_available=is_available,
                form=form,
                # TODO: Add translation
                title=_("Edit page %s") % repr(p.title),
                upload_path=rel_path,
            )
            return render(request, 'pages/page_edit.html', context=context)
        else:
            form = EditForm(request.POST, instance=p)
            #
            save = request.POST.get("save")
            preview = request.POST.get("preview")
            #
            if save is not None:
                if form.is_valid():
                    form.instance.prepare_save(request)
                    page = form.save()
                    if page.save_needed:
                        messages.edit_success(request)
                        # update search index
                        update_item(page)
                    else:
                        messages.no_change(request)
                else:
                    messages.internal_error(request)
                return HttpResponseRedirect(url_page(rel_path))
            elif preview is not None:
                context_adaption(
                    context,
                    request,
                    rel_path=rel_path,
                    is_available=is_available,
                    form=form,
                    # TODO: Add translation
                    title=_("Edit page %s") % repr(p.title),
                    upload_path=rel_path,
                    page_content=p.render_text(request, form.data.get("page_txt"))
                )
                return render(request, 'pages/page_edit.html', context=context)
            else:
                return HttpResponseRedirect(url_page(rel_path))
    else:
        messages.permission_denied_msg_page(request, rel_path)
        return HttpResponseRedirect(url_page(rel_path))


def delete(request, rel_path):
    acc = access_control(request, rel_path)
    if acc.may_write():
        context = Context(request)      # needs to be executed first because of time mesurement
        #
        try:
            p = PikiPage.objects.get(rel_path=rel_path)
            is_available = True
        except PikiPage.DoesNotExist:
            p = PikiPage(rel_path=rel_path)
            is_available = False
        #
        if not request.POST:
            #
            # form = DeleteForm(page_data=p.raw_page_src, page_tags=p.tags)
            #
            context_adaption(
                context,
                request,
                rel_path=rel_path,
                is_available=is_available,
                # TODO: Add translation
                title=_("Delete page %s") % repr(p.title),
                upload_path=rel_path,
                page_content=p.render_to_html(request),
            )
        else:
            delete = request.POST.get("delete")
            #
            if delete:
                p.deleted = True
                p.save()
                # delete page from search index
                ix = load_index()
                delete_item(ix, p)
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
    acc = access_control(request, rel_path)
    if acc.may_write():
        context = Context(request)      # needs to be executed first because of time mesurement
        #
        try:
            p = PikiPage.objects.get(rel_path=rel_path)
            is_available = True
        except PikiPage.DoesNotExist:
            p = PikiPage(rel_path=rel_path)
            is_available = False
        #
        if not request.POST:
            form = RenameForm(page_name=p.rel_path)
            #
            context_adaption(
                context,
                request,
                rel_path=rel_path,
                is_available=is_available,
                form=form,
                # TODO: Add translation
                title=_("Delete page %s") % repr(p.title),
                upload_path=rel_path,
                page_content=p.render_to_html(request),
            )
        else:
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
                    p.rel_path = page_name
                    p.save()
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
    pl = page_list([PikiPage.objects.get(rel_path=rel_path) for rel_path in set(sr)])
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
