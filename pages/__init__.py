from django.urls.base import reverse


def url_page(request, rel_path):
    return reverse('page-page', kwargs={'rel_path': rel_path})


def url_helpview(request, page):
    return reverse('page-helpview', kwargs={'page': page})


def url_edit(request, rel_path):
    return reverse('page-edit', kwargs={'rel_path': rel_path})


def get_search_query(request):
    return request.GET.get('q')
