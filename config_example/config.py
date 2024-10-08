#######################################################################
# Configuration of your django application
#######################################################################
#
# Piki Setting
#
STARTPAGE = "startpage"

#
# Users library
#
# This enables or disables the self registration
USERS_SELF_REGISTRATION = False

#
# Themes library
#
# This defines the default theme, if no theme is set in the django parameters
DEFAULT_THEME = 'clear-blue'

#
# Django
#
# This defines the mode of the running server
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# This a the secret key for your application.
# SECURITY WARNING: don't run with a dummy secret in production! And don't let others read this key!
SECRET_KEY = None

# This defines the listener hostnames for your django server
# SECURITY WARNING: don't run with '0.0.0.0' in in production, unless you know what you are doing!
# ALLOWED_HOSTS = ['<YOUR_SERVER_HOSTNAME>', ]

# This might be needed for usage in a docker environment
# CSRF_TRUSTED_ORIGINS = ['<YOUR_SERVER_URL>', ]
