#######################################################################
# Configuration of your django application
#######################################################################
#
# Piki Setting
#
# The root page to be used
STARTPAGE = "startpage"
# Activate content management system (view)
# CMS_MODE = True

#
# Users library
#
# This enables or disables the self registration
# If you enable self registration it is recommended to configure "Django mail / smtp settings"
USERS_SELF_REGISTRATION = False
# This enables or disables the mail validation after self registration
USERS_MAIL_VALIDATION = True
# This enables or disables the account activation by an admin after self registration
USERS_ADMIN_ACTIVATION = True

#
# Django mail / smtp settings
#
# The hostname of the smtp server
# EMAIL_HOST = "<smtp_host>"
# The port used for the smtp connection
# EMAIL_PORT = <port_number>
# The username for smtp authentication
# EMAIL_HOST_USER = "<smtp_user>"
# The password for smtp authentication
# EMAIL_HOST_PASSWORD = "<smtp_password>"
# The sender of piki emails
# EMAIL_FROM = "piki@<host>"
# Set to True, if TLS shall be used
# EMAIL_USE_TLS = False
# Set to True, if SSL shall be used
# EMAIL_USE_SSL = True
# The smtp timeout
# EMAIL_TIMEOUT =
# Define a ssl keyfile
# EMAIL_SSL_KEYFILE =
# Define an ssl certificate
# EMAIL_SSL_CERTFILE =

#
# Themes library
#
# This defines the default theme, if no theme is set in the django parameters
DEFAULT_THEME = 'clear-teal'

#
# Django
#
# This defines the mode of the running server
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# This a the secret key for your application.
# SECURITY WARNING: don't run with a dummy secret in production! And don't let others read this key!
SECRET_KEY = None

# Define the administrators (for mail delivery)
ADMINS = [("Piki", EMAIL_FROM), ]


# This defines the listener hostnames for your django server
# SECURITY WARNING: don't run with '0.0.0.0' in in production, unless you know what you are doing!
# ALLOWED_HOSTS = ['<YOUR_SERVER_HOSTNAME>', ]

# This might be needed for usage in a docker environment
# CSRF_TRUSTED_ORIGINS = ['<YOUR_SERVER_URL>', ]
