"""
Django settings for piki project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

import config
from logging.handlers import SocketHandler as _SocketHandler
import os
import random
import stat
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = [
    'pages.apps.PagesConfig',
    'themes.apps.ThemesConfig',
    'mycreole.apps.MycreoleConfig',
    'users.apps.UsersConfig',
    #
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #
    'simple_history',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'piki.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'piki.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'data', 'static')
STATIC_URL = 'static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'data', 'media')
MEDIA_URL = '/media/'

MYCREOLE_ROOT = os.path.join(BASE_DIR, 'data', 'mycreole')
MYCREOLE_ATTACHMENT_ACCESS = {
    'read': 'pages.access.read_attachment',
    'modify': 'pages.access.modify_attachment',
}
MYCREOLE_BAR = {
    'navibar': 'pages.context.navigationbar',
    'menubar': 'pages.context.menubar',
}

SYSTEM_PAGES_ROOT = os.path.join(BASE_DIR, 'data', 'system-pages')
PAGES_ROOT = os.path.join(BASE_DIR, 'data', 'pages')

WHOOSH_PATH = os.path.join(BASE_DIR, 'data', 'whoosh')

LOGIN_URL = 'users-login'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Check permission of config.py
#
if sys.platform == 'linux' or sys.platform == 'linux2':
    st = os.stat(os.path.join(BASE_DIR, 'config.py'))
    if st.st_mode & stat.S_IRGRP or st.st_mode & stat.S_IROTH:
        raise PermissionError("conig.py is readable by group or others.")

# Default values, if not defined in config.py
#
USER_CONFIG_DEFAULTS = {
    'DEBUG': False,
    'SECRET_KEY': None,
    'DEFAULT_THEME': 'clear-blue',
    'ALLOWED_HOSTS': ['127.0.0.1', 'localhost', ],
    'CSRF_TRUSTED_ORIGINS': [],
    'ADMINS': [],
    #
    'EMAIL_HOST': None,
    'EMAIL_PORT': None,
    'EMAIL_HOST_USER': None,
    'EMAIL_FROM': "piki",
    'EMAIL_HOST_PASSWORD': None,
    'EMAIL_USE_TLS': None,
    'EMAIL_USE_SSL': None,
    'EMAIL_TIMEOUT': None,
    'EMAIL_SSL_KEYFILE': None,
    'EMAIL_SSL_CERTFILE': None,
}

# Set configuration parameters
#
thismodule = sys.modules[__name__]
for property_name in USER_CONFIG_DEFAULTS:
    try:
        value = getattr(config, property_name)
        setattr(thismodule, property_name, value)
    except AttributeError:
        if not property_name.startswith('EMAIL_') or property_name == 'EMAIL_FROM':
            value = USER_CONFIG_DEFAULTS[property_name]
            setattr(thismodule, property_name, value)


# SECURITY WARNING: keep the secret key used in production secret!
#
if SECRET_KEY is None:
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    s_key = ''.join([random.choice(chars) for n in range(50)])
    secret_key_warning = "You need to create a config.py file including at least a SECRET_KEY definition (e.g.: --> %s <--)." % repr(s_key)
    raise KeyError(secret_key_warning)


# Logging Configuration
#
ROOT_LOGGER_NAME = os.path.basename(os.path.dirname(__file__))
default_handler = ['socket', 'console'] if DEBUG else ['console']


class DjangoSocketHandler(_SocketHandler):
    def emit(self, record):
        if hasattr(record, 'request'):
            record.request = None
        return super().emit(record)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'short': {
            'format': "%(asctime)s \"%(name)s - %(levelname)s - %(message)s\"",
            'datefmt': '[%d/%b/%Y %H:%M:%S]',
        },
        'long': {
            'format': """~~~~(%(levelname)-10s)~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
File "%(pathname)s", line %(lineno)d, in %(funcName)s
%(asctime)s: %(name)s - %(message)s
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~""",
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'short',
        },
        'socket': {
            'level': 'DEBUG',
            'class': f'{ROOT_LOGGER_NAME}.settings.DjangoSocketHandler',
            'host': '127.0.0.1',
            'port': 19996,
        },
    },
    'loggers': {
        'django': {
            'handlers': default_handler,
            'level': 'INFO',
            'propagate': False,
        },
        ROOT_LOGGER_NAME: {
            'handlers': default_handler,
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}
