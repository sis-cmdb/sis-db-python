from distutils.core import setup

import sisdb

setup (
    name='sisdb',
    version=sisdb.VERSION,
    description='SIS ORM like library',
    packages=['sisdb'],
    install_requires=['sis >= 0.4']
)
