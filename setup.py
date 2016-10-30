# Always prefer setuptools over distutils
import os
from setuptools import setup, find_packages

version = "0.0.1"

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='transcroobie',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=version,

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(),
    include_package_data=True,

    author='Armin Samii',

    url='https://github.com/artoonie/transcroobie',

    entry_points={
        'console_scripts': [
            'poppy=poppy.Poppy:main',
            'papika=poppy.Poppy:main',
            'bui=poppy.bui:main',
            'bsInstall.py=poppy.util.bsInstall:main',
            'updateDependencies.py=poppy.updateDependencies:main'
        ],
    },
    scripts=[ ],
    install_requires=['django',
                      'gunicorn',
                      'whitenoise',
                      'pydub',
                      'boto',
                      'dj-database-url',
                      'psycopg2',
                      'django-storages',
                      'google-api-python-client']
)
