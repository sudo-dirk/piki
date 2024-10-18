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
import users

urlpatterns = [
    path('admin/', admin.site.urls),
    #
    # page
    path('', pages.views.root, name='page-root'),
    path('page/', pages.views.root, name='page-root'),
    path('page/<path:rel_path>', pages.views.page, name='page-page'),
    path('pageedit/<path:rel_path>/', pages.views.edit, name='page-edit'),
    path('pagedelete/<path:rel_path>/', pages.views.delete, name='page-delete'),
    path('pagerename/<path:rel_path>/', pages.views.rename, name='page-rename'),
    path('helpview/', pages.views.helpview, name='page-helpview'),
    path('helpview/<str:page>', pages.views.helpview, name='page-helpview'),
    # theme
    path('search/', pages.views.search, name='search'),
    # mycreole
    path('mycreole/', include('mycreole.urls')),
    # users
    path('users/', include('users.urls')),
    path('login/', users.views.login, name='users-login-root'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
