from django.conf import settings

import mycreole
import os


class page(object):
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

    def __read_content__(self):
        if self.is_available():
            with open(self.content_file_name, 'r') as fh:
                return fh.read()
        else:
            # TODO: Create message for creation or no content dependent of user has write access
            return "Page not available. Create it."

    def render_to_html(self, request):
        return mycreole.render(request, self.__read_content__(), self.attachment_path, "next_anchor")
