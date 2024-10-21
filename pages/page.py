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


class base(dict):
    @property
    def rel_path(self):
        return os.path.basename(self._path).replace(2*SPLITCHAR, "/")

    def is_available(self):
        is_a = os.path.isfile(self.filename)
        if not is_a:
            logger.debug("Not available - %s", self.filename)
        return is_a

    def history_numbers_list(self):
        history_folder = os.path.join(self._path, HISTORY_FOLDER_NAME)
        return list(set([int(os.path.basename(filename)[:5]) for filename in fstools.filelist(history_folder)]))


class meta_data(base):
    META_FILE_NAME = 'meta.json'
    #
    KEY_CREATION_TIME = "creation_time"
    KEY_CREATION_USER = "creation_user"
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
                #
                if self.KEY_CREATION_USER not in self:
                    self[self.KEY_CREATION_USER] = self[self.KEY_MODIFIED_USER]
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


class page_data(base):
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
        # Page
        self._page = page_data(page_path, history_version=history_version)
        self._page_meta = meta_data(page_path, history_version=history_version)

    def __page_path__(self, path):
        if path.startswith(settings.PAGES_ROOT):
            # must be a filesystem path
            return path
        else:
            # must be a relative url
            return os.path.join(settings.PAGES_ROOT, path.replace("/", 2*SPLITCHAR))

    def __page_choose__(self):
        return self._page

    def __meta_choose__(self):
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

    @property
    def creation_user(self):
        meta = self.__meta_choose__()
        rv = meta.get(meta.KEY_CREATION_USER)
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
        return self._page.is_available()

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
        rv = page.render_meta(self.creation_time, self.modified_time, self.creation_user, self.modified_user, self.tags)
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
