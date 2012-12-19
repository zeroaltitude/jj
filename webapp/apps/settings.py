# Django settings for apps project.

import os
#from paypal import PayPalConfig


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'jotjournal'             # Or path to database file if using sqlite3.
DATABASE_USER = 'jotjournal'             # Not used with sqlite3.
DATABASE_PASSWORD = 'jj'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.
# XXX remove me someday (only needed for syncdb when creating tables)
DATABASE_OPTIONS = {
   "init_command": "SET storage_engine=INNODB",
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '2dv_@fdsaa0j^zp1^tn992fdsaijhmg_r=h2xk^k3_$sj4fdsa'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'apps.urls'
ROOT_PATH = os.path.dirname(__file__)

TEMPLATE_DIRS = (
    os.path.join(ROOT_PATH, 'templates')
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',

	'jjmaker',
)


################################################################## app settings

FACEBOOK_APP_ID = '114178038611536'
FACEBOOK_API_KEY = ''
FACEBOOK_SECRET_KEY = ''
CANVAS_URL = 'http://apps.facebook.com/jotjournal/'
FB_ADMINS = [1, '1', '572816695', '9133928']

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'orders@myjotjournal.com'
EMAIL_HOST_PASSWORD = ''

THANKS_EMAIL = """
Dear %s,

I am the founder of JotJournal, and I want to thank you for your order! Your order number is %s and your book will arrive within 2 weeks. If you have any questions about your order, please email us at  help@myjotjournal.com.

I hope you love your JotJournal! I want to make JotJournal the easiest, fastest and most enjoyable way to keep your moments. I always appreciate hearing from customers so please feel free to email me with any feedback, ideas or questions at liesel@myjotjournal.com.

To keep up with the latest news and specials from JotJournal please make sure to "like" us by clicking the Like button on our site or on our fan page at www.facebook.com/jotjournal.

If you love JotJournal, we'd appreciate it if you'd let your friends know!

Thank you!

Liesel Pollvogt
Founder, JotJournal
liesel@myjotjournal.com
"""

SHOP_PREFIX = 'https://myjotjournal.com'
SHOP_SECRET = ''

APP_HOST = 'myjotjournal.com'

DEVELOPMENT_TAG = ""
PROMOTION_ONLY = False
INSECURE_APP = False
STAGING = False

from decimal import *
MA_TAX = Decimal("0.0625")

################################ LIVE VERSION ###################################
#### PayPal WPP
# Enter your test account's API details here. You'll need the 3-token
# credentials, not the certificate stuff.
PAYPAL_RETURN_URL_PREFIX = 'https://myjotjournal.com/jjmaker/shop'
PAYPAL_CANCEL_URL = 'https://myjotjournal.com/jjmaker/' # ?

# The email address of your personal test account. This is typically the
# customer for these tests.
TEST_EMAIL_PERSONAL = 'ed_1290695888_per@abra.ms'
# If you view the details of your personal account, you'll see credit card
# details. Enter the credit card number from there.
TEST_VISA_ACCOUNT_NO = '4111111111111111'
# And the expiration date in the form of MMYY. Note that there are no slashes,
# and single-digit month numbers have a leading 0 (IE: 03 for march).
TEST_VISA_EXPIRATION = '1115'
TEST_CVV2 = '000'
#### PayPal PayFlow Pro
PAYPAL_PARTNER_ID = "PayPal"
PAYPAL_VENDOR_ID = "jotjournal"
PAYPAL_USERNAME = "apiuser"
PAYPAL_PASSWORD = ""
################################################################################

# set up logging
import logging
import logging.handlers

ROOT_LOG_FILENAME = 'log.txt'
SHOP_LOG_FILENAME = 'shop.txt'

ROOT_LOGGER = logging.getLogger('RootLogger')
ROOT_LOGGER.setLevel(logging.DEBUG)
root_handler = logging.handlers.RotatingFileHandler(
               ROOT_LOG_FILENAME, maxBytes=10000000, backupCount=1000)
ROOT_LOGGER.addHandler(root_handler)

SHOP_LOGGER = logging.getLogger('ShopLogger')
SHOP_LOGGER.setLevel(logging.DEBUG)
shop_handler = logging.handlers.RotatingFileHandler(
               SHOP_LOG_FILENAME, maxBytes=10000000, backupCount=1000)
SHOP_LOGGER.addHandler(shop_handler)

################################################################################

# Pull in the local changes.
try:
    from local_settings import *
except ImportError, e:
    pass

