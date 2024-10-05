from django.urls.base import reverse


def url_page(request, rel_path):
    return reverse('pages-pages', kwargs={'rel_path': rel_path})


def url_helpview(request, page):
    return reverse('pages-helpview', kwargs={'page': page})
