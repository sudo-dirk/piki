import config
from django.conf import settings
import importlib
import os

CMS_MODE = "CMS_MODE"


def no_access(*args, **kwargs):
    return False


DEFAULTS = {
    CMS_MODE: False,
}


def __get_object_by_name__(object_name):
    class_data = object_name.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]
    #
    module = importlib.import_module(module_path)
    return getattr(module, class_str)


def get(key):
    # take data from config, settings or defaults
    try:
        data = getattr(config, key)
    except AttributeError:
        try:
            data = getattr(settings, key)
        except AttributeError:
            data = DEFAULTS.get(key)
    return data
