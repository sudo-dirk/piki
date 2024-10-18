import difflib
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


SPLITCHAR = ":"
HISTORY_FOLDER_NAME = 'history'


def full_path_all_pages(expression="*"):
    system_pages = fstools.dirlist(settings.SYSTEM_PAGES_ROOT, expression=expression, rekursive=False)
    system_pages = [os.path.join(settings.PAGES_ROOT, os.path.basename(path)) for path in system_pages]
    pages = fstools.dirlist(settings.PAGES_ROOT, expression=expression, rekursive=False)
    rv = []
    for path in set(system_pages + pages):
        p = page_wrapped(None, path)
        if p.is_available():
            rv.append(path)
    return rv


def full_path_deleted_pages(expression="*"):
    system_pages = fstools.dirlist(settings.SYSTEM_PAGES_ROOT, expression=expression, rekursive=False)
    system_pages = [os.path.join(settings.PAGES_ROOT, os.path.basename(path)) for path in system_pages]
    pages = fstools.dirlist(settings.PAGES_ROOT, expression=expression, rekursive=False)
    rv = []
    for path in set(system_pages + pages):
        p = page_wrapped(None, path)
        if not p.is_available():
            rv.append(path)
    return rv


class meta_data(dict):
    META_FILE_NAME = 'meta.json'
    #
    KEY_CREATION_TIME = "creation_time"
    KEY_MODIFIED_TIME = "modified_time"
    KEY_MODIFIED_USER = "modified_user"
    KEY_TAGS = "tags"

    def __init__(self, path, history_version=None):
        self._path = path
        self._history_version = history_version
        #
        # Load data from disk
        try:
            with open(self.filename, 'r') as fh:
                super().__init__(json.load(fh))
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            super().__init__()

    def delete(self):
        os.remove(self.filename)

    @property
    def filename(self):
        if not self._history_version:
            return os.path.join(self._path, self.META_FILE_NAME)
        else:
            return self.history_filename(self._history_version)

    def history_filename(self, history_version):
        return os.path.join(self._path, HISTORY_FOLDER_NAME, "%05d_%s" % (history_version, self.META_FILE_NAME))

    def update_required(self, tags):
        return tags != self.get(self.KEY_TAGS)

    def update(self, username, tags):
        if self._history_version:
            logger.error("A history version %05d can not be updated!", self._history_version)
            return False
        else:
            if username:
                self[self.KEY_MODIFIED_TIME] = int(time.time())
                self[self.KEY_MODIFIED_USER] = username
                if self.KEY_CREATION_TIME not in self:
                    self[self.KEY_CREATION_TIME] = self[self.KEY_MODIFIED_TIME]
            if tags:
                self[self.KEY_TAGS] = tags
            #
            if username or tags:
                self.save()
            return True

    def save(self):
        if self._history_version:
            logger.error("A history version %05d can not be updated!", self._history_version)
            return False
        else:
            with open(self.filename, 'w') as fh:
                json.dump(self, fh, indent=4)
            return True

    def store_to_history(self, history_number):
        history_filename = self.history_filename(history_number)
        fstools.mkdir(os.path.dirname(history_filename))
        shutil.copy(self.filename, history_filename)


class page_data(object):
    PAGE_FILE_NAME = 'page'

    def __init__(self, path, history_version=None):
        self._history_version = history_version
        self._path = path
        self._raw_page_src = None

    def _load_page_src(self):
        if self._raw_page_src is None:
            try:
                with open(self.filename, 'r') as fh:
                    self._raw_page_src = fh.read()
            except FileNotFoundError:
                self._raw_page_src = ""

    def delete(self):
        os.remove(self.filename)

    def rename(self, page_name):
        # Change backslash to slash and remove double slashes
        page_name = page_name.replace("\\", "/")
        while "//" in page_name:
            page_name = page_name.replace("//", "/")
        # move path
        target_path = os.path.join(settings.PAGES_ROOT, page_name.replace("/", 2*SPLITCHAR))
        shutil.move(self._path, target_path)
        # set my path
        self._path = target_path

    def update_required(self, page_txt):
        return page_txt.replace("\r\n", "\n") != self.raw_page_src

    def update_page(self, page_txt):
        if self._history_version:
            logger.error("A history version %05d can not be updated!", self._history_version)
            return False
        else:
            # save the new page content
            fstools.mkdir(os.path.dirname(self.filename))
            with open(self.filename, 'w') as fh:
                fh.write(page_txt)
            self._raw_page_src = page_txt
            return True

    @property
    def filename(self):
        if not self._history_version:
            return os.path.join(self._path, self.PAGE_FILE_NAME)
        else:
            return self.history_filename(self._history_version)

    def history_filename(self, history_version):
        return os.path.join(self._path, HISTORY_FOLDER_NAME, "%05d_%s" % (history_version, self.PAGE_FILE_NAME))

    @property
    def rel_path(self):
        return os.path.basename(self._path).replace(2*SPLITCHAR, "/")

    def is_available(self):
        is_a = os.path.isfile(self.filename)
        if not is_a:
            logger.debug("page.is_available: Not available - %s", self.filename)
        return is_a

    @property
    def title(self):
        return os.path.basename(self._path).split(2*SPLITCHAR)[-1]

    @property
    def raw_page_src(self):
        self._load_page_src()
        return self._raw_page_src

    def store_to_history(self, history_number):
        history_filename = self.history_filename(history_number)
        fstools.mkdir(os.path.dirname(history_filename))
        shutil.copy(self.filename, history_filename)


class page_django(page_data):
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

    def history_numbers_list(self):
        history_folder = os.path.join(self._path, HISTORY_FOLDER_NAME)
        return list(set([int(os.path.basename(filename)[:5]) for filename in fstools.filelist(history_folder)]))

    def render_meta(self, ctime, mtime, user, tags):
        #
        # Page meta data
        #
        meta = f'=== {_("Meta data")}\n'
        meta += f'|{_("Created")}:|{timestamp_to_datetime(self._request, ctime)}|\n'
        meta += f'|{_("Modified")}:|{timestamp_to_datetime(self._request, mtime)}|\n'
        meta += f'|{_("Editor")}|{user}|\n'
        meta += f'|{_("Tags")}|{tags}|\n'
        #
        # List of hostory page versions
        #
        hnl = self.history_numbers_list()
        if hnl:
            meta += f'=== {_("History")}\n'
            meta += f'| ={_("Version")} | ={_("Date")} | ={_("Page")} | ={_("Meta data")} | \n'
            # Current
            name = _("Current")
            meta += f"| {name} \
                      | {timestamp_to_datetime(self._request, mtime)} \
                      | [[{url_page(self.rel_path)} | Page]] \
                      | [[{url_page(self.rel_path, meta=None)} | Meta]]\n"
            # History
            for num in reversed(hnl):
                p = page_wrapped(self._request, self._path, history_version=num)
                meta += f"| {num} \
                          | {timestamp_to_datetime(self._request, p.modified_time)} \
                          | [[{url_page(p.rel_path, history=num)} | Page]] \
                          | [[{url_page(p.rel_path, meta=None, history=num)} | Meta]] (with page changes)\n"
        # Diff
        html_diff = ""
        if self._history_version:
            meta += f'=== {_("Page differences")}\n'
            #
            c = page_django(self._request, self._path)
            left_lines = c.raw_page_src.splitlines()
            right_lines = self.raw_page_src.splitlines()
            html_diff = difflib.HtmlDiff(wrapcolumn=80).make_table(left_lines, right_lines)
        #
        return mycreole.render_simple(meta) + html_diff

    def render_text(self, request, txt):
        macros = {
            "subpages": self.macro_subpages,
            "allpages": self.macro_allpages,
            "subpagetree": self.macro_subpagetree,
            "allpagestree": self.macro_allpagestree,
        }
        return mycreole.render(request, txt, self.attachment_path, macros=macros)

    def macro_allpages(self, *args, **kwargs):
        kwargs["allpages"] = True
        return self.macro_subpages(*args, **kwargs)

    def macro_subpages(self, *args, **kwargs):
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
        rv = ""
        # create a page_list
        if allpages:
            expression = "*"
            parent_rel_path = ""
        else:
            expression = os.path.basename(self._path) + 2 * SPLITCHAR + "*"
            parent_rel_path = self.rel_path
        #
        pl = page_list(
            self._request,
            [page_django(self._request, path) for path in full_path_all_pages(expression)]
        )
        if tree:
            return "<pre>\n" + page_tree(pl).html() + "</pre>\n"
        else:
            return pl.html_list(depth=depth, filter_str=filter_str, parent_rel_path=parent_rel_path)

    def macro_allpagestree(self, *args, **kwargs):
        kwargs["allpages"] = True
        kwargs["tree"] = True
        return self.macro_subpages(*args, **kwargs)

    def macro_subpagetree(self, * args, **kwargs):
        kwargs["tree"] = True
        return self.macro_subpages(*args, **kwargs)


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
            page = page_wrapped(None, page_path)
            if page.is_available():
                entry = f'<a href="{url_page(page_path)}">{entry}</a>'
            rv += fill + (self.L_PATTERN if l == 0 else self.T_PATTERN) + entry + "\n"
            rv += self.html(page_path, fill=fill+(self.D_PATTERN if l == 0 else self.I_PATTERN))
        return rv


class page_wrapped(object):
    """
    This class holds different page and meta instances and decides which will be used in which case.
    """

    def __init__(self, request, path, history_version=None):
        """_summary_

        Args:
            request (_type_): The django request or None (if None, the page functionality is limited)
            path (_type_): A rel_path of the django page or the filesystem path to the page
            history_version (_type_, optional): The history version of the page to be created
        """
        self._request = request
        #
        page_path = self.__page_path__(path)
        system_page_path = self.__system_page_path__(path)
        # Page
        if request:
            self._page = page_django(request, page_path, history_version=history_version)
        else:
            self._page = page_data(page_path, history_version=history_version)
        self._page_meta = meta_data(page_path, history_version=history_version)
        # System page
        if request:
            self._system_page = page_django(request, system_page_path)
        else:
            self._system_page = page_data(system_page_path)
        self._system_meta_data = meta_data(system_page_path)

    def __page_path__(self, path):
        if path.startswith(settings.PAGES_ROOT):
            # must be a filesystem path
            return path
        else:
            # must be a relative url
            return os.path.join(settings.PAGES_ROOT, path.replace("/", 2*SPLITCHAR))

    def __system_page_path__(self, path):
        return os.path.join(settings.SYSTEM_PAGES_ROOT, os.path.basename(path))

    def __page_choose__(self):
        if not self._page.is_available():
            return self._system_page
        else:
            return self._page

    def __meta_choose__(self):
        if not self._page.is_available():
            return self._system_meta_data
        else:
            return self._page_meta

    def __store_history__(self):
        if self._page.is_available():
            try:
                history_number = max(self._page.history_numbers_list()) + 1
            except ValueError:
                history_number = 1     # no history yet
            self._page.store_to_history(history_number)
            self._page_meta.store_to_history(history_number)

    #
    # meta_data
    #
    @property
    def creation_time(self):
        meta = self.__meta_choose__()
        rv = meta.get(meta.KEY_CREATION_TIME)
        return rv

    def delete(self):
        self.__store_history__()
        self._page.delete()
        self._page_meta.delete()

    @property
    def modified_time(self):
        meta = self.__meta_choose__()
        rv = meta.get(meta.KEY_MODIFIED_TIME)
        return rv

    @property
    def modified_user(self):
        meta = self.__meta_choose__()
        rv = meta.get(meta.KEY_MODIFIED_USER)
        return rv

    def rename(self, page_name):
        self._page.rename(page_name)

    @property
    def tags(self):
        meta = self.__meta_choose__()
        rv = meta.get(meta.KEY_TAGS)
        return rv

    #
    # page
    #
    @property
    def attachment_path(self):
        page = self.__page_choose__()
        rv = page.attachment_path
        return rv

    def is_available(self):
        return self._page.is_available() or self._system_page.is_available()

    def userpage_is_available(self):
        return self._page.is_available()

    @property
    def raw_page_src(self):
        page = self.__page_choose__()
        rv = page.raw_page_src
        return rv

    @property
    def rel_path(self):
        page = self.__page_choose__()
        rv = page.rel_path
        return rv

    def render_meta(self):
        page = self.__page_choose__()
        rv = page.render_meta(self.creation_time, self.modified_time, self.modified_user, self.tags)
        return rv

    def render_to_html(self):
        page = self.__page_choose__()
        rv = page.render_to_html()
        return rv

    def render_text(self, request, txt):
        page = self.__page_choose__()
        rv = page.render_text(request, txt)
        return rv

    @property
    def title(self):
        page = self.__page_choose__()
        rv = page.title
        return rv

    def update_page(self, txt, tags):
        if self._page.update_required(txt) or self._page_meta.update_required(tags):
            rv = False
            # Store history
            self.__store_history__()
            username = None
            if self._page.update_required(txt):
                # Update page
                rv |= self._page.update_page(txt)
                # Identify username, to update meta
                try:
                    if self._request.user.is_authenticated:
                        username = self._request.user.username
                    else:
                        logger.warning("Page edit without having a logged in user. This is not recommended. Check your access definitions!")
                except AttributeError:
                    logger.exception("Page edit without having a request object. Check programming!")
            rv |= self._page_meta.update(username, tags)
            # Update search index
            from pages.search import update_item
            update_item(self)
            return rv
