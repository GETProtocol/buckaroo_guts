import os
import sys

import django
from django.test.utils import get_runner
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'buckaroo.tests.settings'
test_dir = os.path.join(os.path.dirname(__file__), '.')
sys.path.insert(0, test_dir)


def runtests():
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    if hasattr(django, 'setup'):
        django.setup()
    failures = test_runner.run_tests(['buckaroo'])
    sys.exit(bool(failures))

if __name__ == '__main__':
    runtests()