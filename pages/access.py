class access_control(object):
    def __init__(self, request, rel_path):
        self._request = request
        self._rel_path = rel_path

    def may_read(self):
        return "private" not in self._rel_path or self.may_write()

    def may_write(self):
        # /!\ rel_path is the filsystem rel_path - caused by the flat folder structure /!\
        return self._request.user.is_authenticated and self._request.user.username in ['root', 'dirk']

    def may_read_attachment(self):
        return self.may_read()

    def may_modify_attachment(self):
        return self.may_write()


def read_attachment(request, rel_path):
    # Interface for external module mycreole
    return access_control(request, rel_path).may_read_attachment()


def modify_attachment(request, rel_path):
    # Interface for external module mycreole
    return access_control(request, rel_path).may_modify_attachment()
