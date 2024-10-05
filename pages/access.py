# TODO: Implement access control for pages

def read_page(request, rel_path):
    return True


def write_page(request, rel_path):
    return request.user.is_authenticated and request.user.username in ['root', 'dirk']


def read_attachment(request, rel_path):
    return read_page(request, rel_path)


def modify_attachment(request, rel_path):
    return write_page(request, rel_path)
