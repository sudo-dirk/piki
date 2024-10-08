def read_page(request, rel_path):
    return "private" not in rel_path or write_page(request, rel_path)


def write_page(request, rel_path):
    return request.user.is_authenticated and request.user.username in ['root', 'dirk']


def read_attachment(request, rel_path):
    # /!\ rel_path is the filsystem rel_path - caused by the flat folder structure /!\
    return True


def modify_attachment(request, rel_path):
    # /!\ rel_path is the filsystem rel_path - caused by the flat folder structure /!\
    return request.user.is_authenticated and request.user.username in ['root', 'dirk']
