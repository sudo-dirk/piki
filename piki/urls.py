"""
URL configuration for piki project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import pages.views

urlpatterns = [
    path('admin/', admin.site.urls),
    #
    path('', pages.views.root, name='pages-root'),
    path('pages/', pages.views.root, name='pages-root'),
    path('pages/<path:rel_path>', pages.views.pages, name='pages-pages'),
    path('helpview/', pages.views.helpview, name='pages-helpview'),
    path('helpview/<str:page>', pages.views.helpview, name='pages-helpview'),
    path('search/', pages.views.search, name='search'),
    path('mycreole/', include('mycreole.urls')),
    path('users/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
