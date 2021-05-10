# ~*~ coding=utf-8 ~*~

from setuptools import setup

setup(
    name='knv-cli',
    version='0.3',
    description='Provides tools for handling KNV data',
    url='http://github.com/Fundevogel/knv-tools',
    author='Martin Folkers',
    author_email='hello@twobrain.io',
    maintainer='Fundevogel',
    maintainer_email='maschinenraum@fundevogel.de',
    license='MIT',
    py_modules=['knvcli'],
    install_requires=[
        'Click',
        'pandas',
        'pendulum',
        'PyPDF2',
        'xdg',
    ],
    entry_points='''
        [console_scripts]
        knvcli=main:cli
    ''',
    zip_safe=False
)
