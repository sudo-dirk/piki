from django.conf import settings
from django.contrib.auth.models import User, Group
from django.db import models
from django.utils.translation import gettext as _
from simple_history.models import HistoricalRecords

from datetime import datetime
import difflib
import logging
import os
from zoneinfo import ZoneInfo

from users.models import get_userprofile
from pages import url_page

import mycreole

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


class PikiPage(models.Model):
    SAVE_ON_CHANGE_FIELDS = ["rel_path", "page_txt", "tags", "deleted", "owner", "group"]
    #
    rel_path = models.CharField(unique=True, max_length=1000)
    page_txt = models.TextField(max_length=50000)
    tags = models.CharField(max_length=1000, null=True, blank=True)
    deleted = models.BooleanField(default=False)
    #
    creation_time = models.DateTimeField(null=True, blank=True)
    creation_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="creation_user")
    modified_time = models.DateTimeField(null=True, blank=True)
    modified_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="modified_user")
    #
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="owner")
    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL, related_name="group")
    # owner_perms
    owner_perms_read = models.BooleanField(default=True)
    owner_perms_write = models.BooleanField(default=True)
    # group_perms
    group_perms_read = models.BooleanField(default=True)
    group_perms_write = models.BooleanField(default=True)
    # other_perms
    other_perms_read = models.BooleanField(default=True)
    other_perms_write = models.BooleanField(default=False)
    #
    history = HistoricalRecords()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def prepare_save(self, request):
        # Set date
        tmd = datetime.now(tz=ZoneInfo("UTC")).replace(microsecond=0)
        self.creation_time = self.creation_time or tmd
        self.modified_time = tmd
        # Set user
        self.creation_user = self.creation_user or request.user
        self.owner = self.owner or request.user
        self.modified_user = request.user

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.id and not force_update:
            orig = PikiPage.objects.get(id=self.id)
            for key in self.SAVE_ON_CHANGE_FIELDS:
                if getattr(self, key) != getattr(orig, key):
                    break
            else:
                self.save_needed = False
                return False
        self.save_needed = True
        return models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    #
    # Set history datetime to modified datetime
    #
    @property
    def _history_date(self):
        return self.modified_time

    @_history_date.setter
    def _history_date(self, value):
        self.modified_time = value

    #
    # My information
    #
    @property
    def title(self):
        return self.rel_path.split("/")[-1]

    #
    # My methods
    #
    def render_to_html(self, request, history=None):
        if history:
            h = self.history.get(history_id=history)
            return self.render_text(request, h.page_txt)
        else:
            return self.render_text(request, self.page_txt)

    def user_datetime(self, request, dtm):
        try:
            up = get_userprofile(request.user)
        except AttributeError:
            tz = ZoneInfo("UTC")
        else:
            tz = ZoneInfo(up.timezone)
        #
        return datetime.astimezone(dtm, tz)

    def render_meta(self, request, history):
        # Page information
        meta = f'= {_("Meta data")}\n'
        meta += f'|{_("Created by")}:|{self.creation_user}|\n'
        meta += f'|{_("Created at")}:|{self.user_datetime(request, self.creation_time)}|\n'
        meta += f'|{_("Modified by")}:|{self.modified_user}|\n'
        meta += f'|{_("Modified at")}:|{self.user_datetime(request, self.modified_time)}|\n'
        meta += f'|{_("Owner")}:|{self.owner or "---"}|\n'
        meta += f'|{_("Group")}:|{self.group or "---"}|\n'
        meta += f'|{_("Tags")}|{self.tags or "---"}|\n'
        #
        # List of history page versions
        #
        hl = self.history.all()[1:]
        if len(hl) > 0:
            meta += f'= {_("History")}\n'
            meta += f'| ={_("Version")} | ={_("Date")} | ={_("Page")} | ={_("Meta data")} | ={_("Page changed")} | ={_("Tags changed")} | \n'
            # Current
            name = _("Current")
            meta += f"| {name} \
                      | {self.user_datetime(request, self.modified_time)} \
                      | [[{url_page(self.rel_path)} | Page]] \
                      | [[{url_page(self.rel_path, meta=None)} | Meta]] |"
            page_content = self.page_txt.replace("\r\n", "\n").strip("\n")
            tags = self.tags
            for h_page in hl:
                page_changed = page_content != h_page.page_txt.replace("\r\n", "\n").strip("\n")
                tags_changed = tags != h_page.tags
                if page_changed or tags_changed:
                    meta += " %s |" % ("Yes" if page_changed else "No")
                    meta += " %s |" % ("Yes" if tags_changed else "No")
                    meta += "\n"
                    meta += f"| {h_page.history_id} \
                                | {self.user_datetime(request, h_page.modified_time)} \
                                | [[{url_page(self.rel_path, history=h_page.history_id)} | Page]] \
                                | [[{url_page(self.rel_path, meta=None, history=h_page.history_id)} | Meta]] (with diff to current) |"
                    page_content = h_page.page_txt[:].replace("\r\n", "\n").strip("\n")
                    tags = h_page.tags
            meta += " --- | --- |\n"
        # Diff
        html_diff = ""
        if history:
            h_page = self.history.get(history_id=history)
            #
            meta += f'= {_("Page differences")}\n'
            #
            left_lines = self.page_txt.splitlines()
            right_lines = h_page.page_txt.splitlines()
            html_diff = difflib.HtmlDiff(wrapcolumn=80).make_table(left_lines, right_lines, "Current page", "Page Version %d" % history)
        #
        return mycreole.render_simple(meta) + html_diff

    #
    # Creole stuff
    #
    def render_text(self, request, txt):
        macros = {
            "subpages": self.macro_subpages,
            "allpages": self.macro_allpages,
            "subpagetree": self.macro_subpagetree,
            "allpagestree": self.macro_allpagestree,
        }
        return mycreole.render(request, txt, self.rel_path, macros=macros)

    def macro_subpages(self, *args, **kwargs):
        return self.macro_pages(*args, **kwargs)

    def macro_allpages(self, *args, **kwargs):
        kwargs["allpages"] = True
        return self.macro_pages(*args, **kwargs)

    def macro_allpagestree(self, *args, **kwargs):
        kwargs["allpages"] = True
        kwargs["tree"] = True
        return self.macro_pages(*args, **kwargs)

    def macro_subpagetree(self, * args, **kwargs):
        kwargs["tree"] = True
        return self.macro_pages(*args, **kwargs)

    def macro_pages(self, *args, **kwargs):
        allpages = kwargs.pop("allpages", False)
        tree = kwargs.pop("tree", False)
        #

        def parse_depth(s: str):
            try:
                return int(s)
            except ValueError:
                pass

        params = kwargs.get('', '')
        filter_str = ''
        depth = parse_depth(params)
        if depth is None:
            params = params.split(",")
            depth = parse_depth(params[0])
            if len(params) == 2:
                filter_str = params[1]
            elif depth is None:
                filter_str = params[0]
        #
        if not allpages:
            filter_str = os.path.join(self.rel_path, filter_str)
        #
        pages = PikiPage.objects.filter(rel_path__contains=filter_str)
        pl = page_list([p for p in pages if not p.deleted])
        #
        if tree:
            return "<pre>\n" + page_tree(pl).html() + "</pre>\n"
        else:
            return pl.html_list(depth=depth, filter_str=filter_str, parent_rel_path='' if allpages else self.rel_path)


class page_list(list):
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def sort_basename(self):
        return list.sort(self, key=lambda x: os.path.basename(x.rel_path))

    def creole_list(self, depth=None, filter_str='', parent_rel_path=''):
        self.sort_basename()
        depth = depth or 9999   # set a random high value if None
        #
        rv = ""
        last_char = None
        for page in self:
            if page.rel_path.startswith(filter_str) and page.rel_path != filter_str:
                name = page.rel_path[len(parent_rel_path):].lstrip("/")
                if name.count('/') < depth:
                    first_char = os.path.basename(name)[0].upper()
                    if last_char != first_char:
                        last_char = first_char
                        rv += f"=== {first_char}\n"
                    rv += f"* [[{url_page(page.rel_path)} | {name} ]]\n"
        return rv

    def html_list(self, depth=9999, filter_str='', parent_rel_path=''):
        return mycreole.render_simple(self.creole_list(depth, filter_str, parent_rel_path))


class page_tree(dict):
    T_PATTERN = "├── "
    L_PATTERN = "└── "
    I_PATTERN = "│   "
    D_PATTERN = "    "

    def __init__(self, pl: page_list):
        super().__init__()
        for page in pl:
            store_item = self
            for entry in page.rel_path.split("/"):
                if not entry in store_item:
                    store_item[entry] = {}
                store_item = store_item[entry]

    def html(self, rel_path=None, fill=""):
        base = self
        try:
            for key in rel_path.split("/"):
                base = base[key]
        except AttributeError:
            rel_path = ''
        #
        rv = ""
        #
        l = len(base)
        for entry in sorted(list(base.keys())):
            l -= 1
            page_path = os.path.join(rel_path, entry)
            try:
                PikiPage.objects.get(rel_path=page_path)
            except PikiPage.DoesNotExist:
                pass
            else:
                entry = f'<a href="{url_page(page_path)}">{entry}</a>'
            rv += fill + (self.L_PATTERN if l == 0 else self.T_PATTERN) + entry + "\n"
            rv += self.html(page_path, fill=fill+(self.D_PATTERN if l == 0 else self.I_PATTERN))
        return rv
