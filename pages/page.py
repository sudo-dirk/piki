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

    def update(self, username):
        self[self.KEY_MODIFIED_TIME] = int(time.time())
        self[self.KEY_MODIFIED_USER] = username
        #
        self.save()

    def save(self):
        with open(self._meta_filename, 'w') as fh:
            json.dump(self, fh, indent=4)


class base_page(object):
    PAGE_FILE_NAME = 'page'
    META_FILE_NAME = 'meta.json'
    HISTORY_FOLDER_NAME = 'history'
    SPLITCHAR = ":"

    def __init__(self, path):
        if path.startswith(settings.PAGES_ROOT):
            self._path = path
        else:
            self._path = os.path.join(settings.PAGES_ROOT, path.replace("/", 2*self.SPLITCHAR))
        self._raw_page_src = None
        #
        self._meta_data = meta_data(self._meta_filename, self.is_available())

    def _load_page_src(self):
        if self._raw_page_src is None:
            try:
                with open(self.filename, 'r') as fh:
                    self._raw_page_src = fh.read()
            except FileNotFoundError:
                self._raw_page_src = ""

    def _store_history(self):
        history_folder = os.path.join(self._path, self.HISTORY_FOLDER_NAME)
        # create folder if needed
        fstools.mkdir(history_folder)
        # identify last_history number
        flist = fstools.filelist(history_folder)
        flist.sort()
        if flist:
            hist_number = int(os.path.basename(flist[-1])[:5]) + 1
        else:
            hist_number = 1
        # copy file to history folder
        shutil.copy(self.filename, os.path.join(history_folder, "%05d_%s" % (hist_number, self.PAGE_FILE_NAME)))
        shutil.copy(self._meta_filename, os.path.join(history_folder, "%05d_%s" % (hist_number, self.META_FILE_NAME)))

    def update_page(self, page_txt):
        from .search import update_item
        if page_txt.replace("\r\n", "\n") != self.raw_page_src:
            # Store page history
            if self.raw_page_src:
                self._store_history()
            # save the new page content
            fstools.mkdir(os.path.dirname(self.filename))
            with open(self.filename, 'w') as fh:
                fh.write(page_txt)
            # update search index
            update_item(self)
            # update metadata
            self._update_metadata()
            return True
        return False

    @property
    def filename(self):
        return os.path.join(self._path, self.PAGE_FILE_NAME)

    @property
    def _meta_filename(self):
        return os.path.join(self._path, self.META_FILE_NAME)

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

    def _update_metadata(self):
        username = None
        try:
            if self._request.user.is_authenticated:
                username = self._request.user.username
            else:
                logger.warning("Page edit without having a logged in user. This is not recommended. Check your access definitions!")
        except AttributeError:
            logger.exception("Page edit without having a request object. Check programming!")
        self._meta_data.update(username)


class creole_page(base_page):
    FOLDER_ATTACHMENTS = "attachments"

    def __init__(self, request, path) -> None:
        self._request = request
        super().__init__(path)

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
        #
        meta = f'|{_("Created")}:|{ctime}|\n'
        meta += f'|{_("Modified")}:|{mtime}|\n'
        meta += f'|{_("Editor")}|{user}|\n\n'
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
