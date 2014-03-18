from distutils.core import setup

import sisdb

setup (
    name='sisdb',
    version='0.1',
    description='SIS ORM like library',
    packages=['sisdb'],
    install_requires=['sis >= 0.4']
)

