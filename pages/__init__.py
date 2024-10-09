from django.urls.base import reverse


def url_page(request, rel_path, **kwargs):
    params = "&".join([f"{key}" + ("" if kwargs[key] is None else f"={kwargs[key]}") for key in kwargs])
    if len(params) > 0:
        params = "?" + params
    return reverse('page-page', kwargs={'rel_path': rel_path}) + params


def url_helpview(request, page):
    return reverse('page-helpview', kwargs={'page': page})


def url_edit(request, rel_path):
    return reverse('page-edit', kwargs={'rel_path': rel_path})


def get_search_query(request):
    return request.GET.get('q')
