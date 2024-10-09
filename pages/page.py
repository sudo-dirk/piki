from django.conf import settings

import fstools
import logging
from pages import messages, url_page
import mycreole
import os

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


class base_page(object):
    FOLDER_CONTENT = 'content'
    FILE_NAME = 'page'
    SPLITCHAR = ":"

    def __init__(self, path):
        if path.startswith(settings.PAGES_ROOT):
            self._path = path
        else:
            self._path = os.path.join(settings.PAGES_ROOT, path.replace("/", 2*self.SPLITCHAR))
        self._raw_page_src = None

    def _load_page_src(self):
        if self._raw_page_src is None:
            try:
                with open(self.filename, 'r') as fh:
                    self._raw_page_src = fh.read()
            except FileNotFoundError:
                self._raw_page_src = ""

    def update_page(self, page_txt):
        from .search import update_item
        #
        folder = os.path.dirname(self.filename)
        if not os.path.exists(folder):
            fstools.mkdir(folder)
        with open(self.filename, 'w') as fh:
            fh.write(page_txt)
        update_item(self)

    @property
    def filename(self):
        return os.path.join(self._path, self.FOLDER_CONTENT, self.FILE_NAME)

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
        startname = ''
        depth = parse_depth(params)
        if depth is None:
            params = params.split(",")
            depth = parse_depth(params[0])
            if len(params) == 2:
                startname = params[1]
            elif depth is None:
                startname = params[0]
            if depth is None:
                depth = 9999
        #
        rv = ""
        # create a rel_path list
        pathlist = [base_page(path).rel_path for path in fstools.dirlist(settings.PAGES_ROOT, rekursive=False)]
        # sort basename
        pathlist.sort(key=os.path.basename)

        last_char = None
        for contentname in pathlist:
            #
            if (contentname.startswith(self.rel_path) or allpages) and contentname != self.rel_path:
                if allpages:
                    name = contentname
                else:
                    name = contentname[len(self.rel_path)+1:]
                if name.count('/') < depth and name.startswith(startname):
                    if last_char != os.path.basename(name)[0].upper():
                        last_char = os.path.basename(name)[0].upper()
                        if last_char is not None:
                            rv += "</ul>\n"
                        rv += f'<h3>{last_char}</h3>\n<ul>\n'
                    rv += f'  <li><a href="{url_page(self._request, contentname)}">{name}</a></li>\n'
        if len(rv) > 0:
            rv += "</ul>\n"
        return rv
