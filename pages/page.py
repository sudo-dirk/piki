from django.conf import settings
from django.utils.translation import gettext as _
import fstools
import json
import logging
from pages import messages, url_page
import mycreole
import os
import shutil
import time
from . import timestamp_to_datetime

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


class meta_data(dict):
    KEY_CREATION_TIME = "creation_time"
    KEY_MODIFIED_TIME = "modified_time"
    KEY_MODIFIED_USER = "modified_user"
    KEY_TAGS = "tags"

    def __init__(self, meta_filename, page_exists):
        self._meta_filename = meta_filename

        # Load data from disk
        try:
            with open(meta_filename, 'r') as fh:
                super().__init__(json.load(fh))
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            super().__init__()

        # Add missing information to meta_data
        missing_keys = False
        if self.KEY_CREATION_TIME not in self:
            missing_keys = True
            self[self.KEY_CREATION_TIME] = int(time.time())
        if self.KEY_MODIFIED_TIME not in self:
            self[self.KEY_MODIFIED_TIME] = self[self.KEY_CREATION_TIME]
        if missing_keys and page_exists:
            self.save()

    def update(self, username, tags):
        if username:
            self[self.KEY_MODIFIED_TIME] = int(time.time())
            self[self.KEY_MODIFIED_USER] = username
        if tags:
            self[self.KEY_TAGS] = tags
        #
        if username or tags:
            self.save()

    def save(self):
        with open(self._meta_filename, 'w') as fh:
            json.dump(self, fh, indent=4)


class base_page(object):
    PAGE_FILE_NAME = 'page'
    META_FILE_NAME = 'meta.json'
    HISTORY_FOLDER_NAME = 'history'
    SPLITCHAR = ":"

    def __init__(self, path, history_version=None):
        self._history_version = history_version
        #
        if path.startswith(settings.PAGES_ROOT):
            self._path = path
        else:
            self._path = os.path.join(settings.PAGES_ROOT, path.replace("/", 2*self.SPLITCHAR))
        self._raw_page_src = None
        #
        self._meta_data = meta_data(self._meta_filename, self.is_available())

    @property
    def modified_time(self):
        return self._meta_data.get(self._meta_data.KEY_MODIFIED_TIME)

    def _load_page_src(self):
        if self._raw_page_src is None:
            try:
                with open(self.filename, 'r') as fh:
                    self._raw_page_src = fh.read()
            except FileNotFoundError:
                self._raw_page_src = ""

    def history_numbers_list(self):
        history_folder = os.path.join(self._path, self.HISTORY_FOLDER_NAME)
        fstools.mkdir(history_folder)
        # identify last_history number
        return list(set([int(os.path.basename(filename)[:5]) for filename in fstools.filelist(history_folder)]))

    def _store_history(self):
        try:
            hist_number = max(self.history_numbers_list()) + 1
        except ValueError:
            hist_number = 1     # no history yet
        # copy file to history folder
        shutil.copy(self.filename, self.history_filename(hist_number))
        shutil.copy(self._meta_filename, self._history_meta_filename(hist_number))

    def update_page(self, page_txt, tags):
        if self._history_version:
            logger.error("A history version %05d can not be updated!", self._history_version)
            return False
        else:
            from .search import update_item
            if page_txt.replace("\r\n", "\n") != self.raw_page_src:
                # Store page history
                if self.raw_page_src:
                    self._store_history()
                # save the new page content
                fstools.mkdir(os.path.dirname(self.filename))
                with open(self.filename, 'w') as fh:
                    fh.write(page_txt)
                # update metadata
                page_changed = True
            else:
                page_changed = False
            self._update_metadata(tags)
            # update search index
            update_item(self)
            return page_changed

    @property
    def filename(self):
        if not self._history_version:
            return os.path.join(self._path, self.PAGE_FILE_NAME)
        else:
            return self.history_filename(self._history_version)

    def history_filename(self, history_version):
        return os.path.join(self._path, self.HISTORY_FOLDER_NAME, "%05d_%s" % (history_version, self.PAGE_FILE_NAME))

    @property
    def _meta_filename(self):
        if not self._history_version:
            return os.path.join(self._path, self.META_FILE_NAME)
        else:
            return self._history_meta_filename(self._history_version)

    def _history_meta_filename(self, history_version):
        return os.path.join(self._path, self.HISTORY_FOLDER_NAME, "%05d_%s" % (history_version, self.META_FILE_NAME))

    @property
    def rel_path(self):
        return os.path.basename(self._path).replace(2*self.SPLITCHAR, "/")

    def rel_path_is_valid(self):
        return not self.SPLITCHAR in self.rel_path

    def is_available(self):
        is_a = os.path.isfile(self.filename)
        if not is_a:
            logger.info("page.is_available: Not available - %s", self.filename)
        return is_a

    @property
    def title(self):
        return os.path.basename(self._path).split("::")[-1]

    @property
    def raw_page_src(self):
        self._load_page_src()
        return self._raw_page_src

    def _update_metadata(self, tags):
        username = None
        try:
            if self._request.user.is_authenticated:
                username = self._request.user.username
            else:
                logger.warning("Page edit without having a logged in user. This is not recommended. Check your access definitions!")
        except AttributeError:
            logger.exception("Page edit without having a request object. Check programming!")
        self._meta_data.update(username, tags)

    @property
    def page_tags(self):
        return self._meta_data.get(self._meta_data.KEY_TAGS)


class creole_page(base_page):
    FOLDER_ATTACHMENTS = "attachments"

    def __init__(self, request, path, history_version=None) -> None:
        self._request = request
        super().__init__(path, history_version=history_version)

    @property
    def attachment_path(self):
        return os.path.join(os.path.basename(self._path), self.FOLDER_ATTACHMENTS)

    def render_to_html(self):
        if self.is_available():
            return self.render_text(self._request, self.raw_page_src)
        else:
            messages.unavailable_msg_page(self._request, self.rel_path)
            return ""

    def render_meta(self):
        ctime = timestamp_to_datetime(self._request, self._meta_data.get(self._meta_data.KEY_CREATION_TIME)).strftime('%Y-%m-%d %H:%M')
        mtime = timestamp_to_datetime(self._request, self._meta_data.get(self._meta_data.KEY_MODIFIED_TIME)).strftime('%Y-%m-%d %H:%M')
        user = self._meta_data.get(self._meta_data.KEY_MODIFIED_USER)
        tags = self._meta_data.get(self._meta_data.KEY_TAGS, "-")
        #
        meta = f'=== {_("Meta data")}\n'
        meta += f'|{_("Created")}:|{ctime}|\n'
        meta += f'|{_("Modified")}:|{mtime}|\n'
        meta += f'|{_("Editor")}|{user}|\n'
        meta += f'|{_("Tags")}|{tags}|\n'
        #
        hnl = self.history_numbers_list()
        if hnl:
            meta += f'=== {_("History")}\n'
            meta += f'| ={_("Version")} | ={_("Date")} | ={_("Page")} | ={_("Meta data")} | \n'
            # Current
            name = _("Current")
            meta += f"| {name} \
                      | {timestamp_to_datetime(self._request, self.modified_time)} \
                      | [[{url_page(self._request, self.rel_path)} | Page]] \
                      | [[{url_page(self._request, self.rel_path, meta=None)} | Meta]]\n"
            # History
            for num in reversed(hnl):
                p = creole_page(self._request, self._path, history_version=num)
                meta += f"| {num} \
                          | {timestamp_to_datetime(self._request, p.modified_time)} \
                          | [[{url_page(self._request, p.rel_path, history=num)} | Page]] \
                          | [[{url_page(self._request, p.rel_path, meta=None, history=num)} | Meta]]\n"
        #
        meta += f'=== {_("Page content")}\n'
        if not self._history_version:
            meta += '{{{\n%s\n}}}\n' % self.raw_page_src
        else:
            c = creole_page(self._request, self.rel_path)
            meta += "| =Current | =This |\n"
            left_lines = c.raw_page_src.splitlines()
            right_lines = self.raw_page_src.splitlines()
            while len(left_lines) + len(right_lines) > 0:
                try:
                    left = left_lines.pop(0)
                except IndexError:
                    left = ""
                try:
                    right = right_lines.pop(0)
                except IndexError:
                    right = ""
                if left == right:
                    meta += "| {{{ %s }}} | {{{ %s }}} |\n" % (left, right)
                else:
                    meta += "| **{{{ %s }}}** | **{{{ %s }}}** |\n" % (left, right)
        #
        return mycreole.render_simple(meta)

    def render_text(self, request, txt):
        macros = {
            "subpages": self.macro_subpages,
            "allpages": self.macro_allpages,
        }
        return mycreole.render(request, txt, self.attachment_path, macros=macros)

    def macro_allpages(self, *args, **kwargs):
        kwargs["allpages"] = True
        return self.macro_subpages(*args, **kwargs)

    def macro_subpages(self, *args, **kwargs):
        allpages = kwargs.pop("allpages", False)
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
        rv = ""
        # create a page_list
        if allpages:
            expression = "*"
            parent_rel_path = ""
        else:
            expression = os.path.basename(self._path) + 2 * self.SPLITCHAR + "*"
            parent_rel_path = self.rel_path
        pl = page_list(
            self._request,
            [creole_page(self._request, path) for path in fstools.dirlist(settings.PAGES_ROOT, expression=expression, rekursive=False)]
        )
        return pl.html_list(depth=depth, filter_str=filter_str, parent_rel_path=parent_rel_path)


class page_list(list):
    def __init__(self, request, *args, **kwargs):
        self._request = request
        return super().__init__(*args, **kwargs)

    def sort_basename(self):
        return list.sort(self, key=lambda x: os.path.basename(x.rel_path))

    def creole_list(self, depth=None, filter_str='', parent_rel_path=''):
        self.sort_basename()
        depth = depth or 9999   # set a random high value if None
        #
        parent_rel_path = parent_rel_path + "/" if len(parent_rel_path) > 0 else ""
        #
        rv = ""
        last_char = None
        for page in self:
            name = page.rel_path[len(parent_rel_path):]
            if name.startswith(filter_str) and name != filter_str:
                if name.count('/') < depth:
                    first_char = os.path.basename(name)[0].upper()
                    if last_char != first_char:
                        last_char = first_char
                        rv += f"=== {first_char}\n"
                    rv += f"* [[{url_page(self._request, page.rel_path)} | {name} ]]\n"
        return rv

    def html_list(self, depth=9999, filter_str='', parent_rel_path=''):
        return mycreole.render_simple(self.creole_list(depth, filter_str, parent_rel_path))
