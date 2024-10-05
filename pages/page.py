from django.conf import settings

import fstools
from pages import messages
import mycreole
import os


class creol_page(object):
    SPLITCHAR = ":"
    FOLDER_ATTACHMENTS = "attachments"
    FOLDER_CONTENT = 'content'
    FILE_NAME = 'page'

    def __init__(self, rel_path) -> None:
        self._rel_path = rel_path

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

    @property
    def content_folder_name(self):
        return self._rel_path.replace('/', '::')

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

    def render_to_html(self, request):
        if self.is_available():
            return mycreole.render(request, self.raw_page_src, self.attachment_path, "next_anchor")
        else:
            messages.unavailable_msg_page(request, self._rel_path)
            return ""
