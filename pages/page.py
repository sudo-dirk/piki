from django.conf import settings

# TODO: PRIO: BugFix if subpages filter is used without parameters
# TODO: PRIO: Add wildcards for subpages filter
# TODO: Add whoosh and search

import fstools
from pages import messages, url_page
import mycreole
import os


class creol_page(object):
    SPLITCHAR = ":"
    FOLDER_ATTACHMENTS = "attachments"
    FOLDER_CONTENT = 'content'
    FILE_NAME = 'page'

    def __init__(self, request, rel_path) -> None:
        self._rel_path = rel_path
        self._request = request

    def rel_path_is_valid(self):
        return not self.SPLITCHAR in self._rel_path

    def is_available(self):
        return os.path.isfile(self.content_file_name)

    @property
    def title(self):
        return os.path.basename(self._rel_path)

    @property
    def attachment_path(self):
        return os.path.join(self.content_folder_name, self.FOLDER_ATTACHMENTS)

    def __content_folder_filter__(self, folder):
        return folder.replace('/', '::')

    def __folder_content_filter__(self, folder):
        return folder.replace('::', '/')

    @property
    def content_folder_name(self):
        return self.__content_folder_filter__(self._rel_path)

    @property
    def content_file_name(self):
        return os.path.join(settings.PAGES_ROOT, self.content_folder_name, self.FOLDER_CONTENT, self.FILE_NAME)

    @property
    def raw_page_src(self):
        try:
            with open(self.content_file_name, 'r') as fh:
                return fh.read()
        except FileNotFoundError:
            return ""

    def update_page(self, page_txt):
        folder = os.path.dirname(self.content_file_name)
        if not os.path.exists(folder):
            fstools.mkdir(folder)
        with open(self.content_file_name, 'w') as fh:
            fh.write(page_txt)

    def render_to_html(self):
        if self.is_available():
            return self.render_text(self._request, self.raw_page_src)
        else:
            messages.unavailable_msg_page(self._request, self._rel_path)
            return ""

    def render_text(self, request, txt):
        macros = {
            "subpages": self.macro_subpages
        }
        return mycreole.render(request, txt, self.attachment_path, macros=macros)

    def macro_subpages(self, *args, **kwargs):
        def parse_depth(s: str):
            try:
                return int(s)
            except ValueError:
                pass

        params = kwargs.get('', '').split(",")
        depth = parse_depth(params[0])
        if len(params) == 2:
            startname = params[1]
        elif depth is None:
            startname = params[0]
        if depth is None:
            depth = 9999
        #
        rv = ""
        pathlist = fstools.dirlist(settings.PAGES_ROOT, rekursive=False)
        pathlist.sort()
        for path in pathlist:
            contentname = self.__folder_content_filter__(os.path.basename(path))
            #
            if contentname.startswith(self._rel_path) and contentname != self._rel_path:
                name = contentname[len(self._rel_path)+1:]
                if name.count('/') <= depth and name.startswith(startname):
                    rv += f'  <li><a href="{url_page(self._request, contentname)}">{name}</a></li>\n'
        if len(rv) > 0:
            rv = "<ul>\n" + rv + "</ul>\n"
        return rv
