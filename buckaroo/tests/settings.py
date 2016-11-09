import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.split(os.path.split(__file__)[0])[0])

ROOT_URLCONF = 'buckaroo.tests.urls'

IS_TEST = 'test' in sys.argv or 'test_coverage' in sys.argv

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
]

MODELS = {
    'Order': 'tests.Order',
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    'actstream',
    'buckaroo.tests',
    'buckaroo'
]

SECRET_KEY = "for-testing-purposes-only-87jhrjkeqhwi8u3o9u9833-0aoi09187u"
ACCOUNT_ACTIVATION_DAYS = 1
SITE_ID = 1
