import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

install_requires = [
    'Django>=1.7.0',
    'djangorestframework>=3.1.0',
    'djangorestframework_jwt>= 1.7.2',
    'six>=1.9.0',
    'django-activity-stream',
    'django_fsm',
    'requests'
]

test_requires = install_requires + [
    'pytest',
    'mock',
    'factory_boy',
    'mock-django'
]

setup(
    name='django-buckaroo',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    tests_require=test_requires,
    test_suite='runtests.runtests',
    license='BSD License',  # example license
    description='A Django application for the Buckaroo API',
    long_description=README,
    url='https://www.guts.org/',
    author='Aksel Ethem',
    author_email='aksel.ethem@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: X.Y',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
