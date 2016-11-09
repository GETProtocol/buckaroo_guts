import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.split(os.path.split(__file__)[0])[0])

ROOT_URLCONF = 'buckaroo.urls'

IS_TEST = 'test' in sys.argv or 'test_coverage' in sys.argv

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

# USE_L10N = True

# USE_TZ = True

TESTING = True

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    # 'Entrails.middleware.AdminOnlyAuthenticationMiddleware',
    # 'Entrails.middleware.AdminOnlySessionMiddleware',
    # 'Entrails.middleware.AdminOnlyCsrf',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

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


