from django.urls.base import reverse

# TODO: Add a filter to show all subpages <<piki-subpages>> and add it to settings and help


"""
def page_link_filter(text):
    render_txt = ''
    while len(text) > 0:
        try:
            pos = text.index('[[page:')
        except ValueError:
            pos = len(text)
        print(pos)
        render_txt += text[:pos]
        text = text[pos + 7:]
        if len(text):
            pos = text.index(']]')
            try:
                rel_path = int(text[:pos])
            except ValueError:
                render_txt += "[[page:" + text[:pos + 2]
            else:
                render_txt += '[[%s|%s]]' % (reverse('pages-pages', kwargs={'rel_path': rel_path}), rel_path)
            text = text[pos + 2:]
    return render_txt
"""
