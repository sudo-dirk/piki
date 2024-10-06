# TODO: Implement access control for pages

def read_page(request, rel_path):
    return True


def write_page(request, rel_path):
    return request.user.is_authenticated and request.user.username in ['root', 'dirk']


def read_attachment(request, rel_path):
    # TODO: /!\ rel_path is the filsystem rel_path - caused by the flat folder structure /!\
    return True


def modify_attachment(request, rel_path):
    # TODO: /!\ rel_path is the filsystem rel_path - caused by the flat folder structure /!\
    return request.user.is_authenticated and request.user.username in ['root', 'dirk']
