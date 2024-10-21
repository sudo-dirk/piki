from django.conf import settings
import logging
import os

from .models import PikiPage

logger = logging.getLogger(settings.ROOT_LOGGER_NAME).getChild(__name__)


class access_control(object):
    def __init__(self, request, rel_path):
        self._request = request
        self._rel_path = rel_path
        self._user = request.user
        try:
            self._page = PikiPage.objects.get(rel_path=rel_path)
        except PikiPage.DoesNotExist:
            self._page = None
        self._read = None
        self._write = None

    def __analyse_access_rights__(self):
        if self._read is None or self._write is None:
            self._read = False
            self._write = False
            #
            if self._user.is_superuser:
                # A superuser has full access
                logger.debug("User is superuser -> full access granted")
                self._read = True
                self._write = True
            elif self._page is None:
                if self._user.is_staff:
                    # Page creation is allowed for staff users
                    logger.debug("Page %s does not exist and user is staff -> full access granted", repr(self._rel_path))
                    self._read = True
                    self._write = True
                else:
                    logger.debug("Page %s does not exist and user is not staff -> no access granted", repr(self._rel_path))
            else:
                user_is_owner = self._page.owner == self._user
                user_in_page_group = self._page.group in self._user.groups.all()
                # read permissions
                if user_is_owner and self._page.owner_perms_read:
                    logger.debug("Read access granted, due to owner permissions of page")
                    self._read = True
                elif user_in_page_group and self._page.group_perms_read:
                    logger.debug("Read access granted, due to group permissions of page")
                    self._read = True
                elif self._page.other_perms_read:
                    logger.debug("Read access granted, due to other permissions of page")
                    self._read = True
                # write permissions
                if user_is_owner and self._page.owner_perms_write:
                    logger.debug("Write access granted, due to owner permissions of page")
                    self._write = True
                elif user_in_page_group and self._page.group_perms_write:
                    logger.debug("Write access granted, due to group permissions of page")
                    self._write = True
                elif self._page.other_perms_write:
                    logger.debug("Write access granted, due to other permissions of page")
                    self._write = True

    def may_read(self):
        self.__analyse_access_rights__()
        return self._read

    def may_write(self):
        self.__analyse_access_rights__()
        return self._write

    def may_read_attachment(self):
        return self.may_read()

    def may_modify_attachment(self):
        return self.may_write()


def read_attachment(request, path):
    # Interface for external module mycreole
    rel_path = os.path.dirname(path)
    return access_control(request, rel_path).may_read_attachment()


def modify_attachment(request, path):
    # Interface for external module mycreole
    rel_path = os.path.dirname(path)
    return access_control(request, rel_path).may_modify_attachment()
