import io
from os.path import abspath, dirname, join
from setuptools import find_packages, setup


VERSION = '0.7'


def long_description():
    readme_file = join(dirname(abspath(__file__)), 'README.md')

    with io.open(readme_file, encoding='utf8') as file:
        return file.read()


setup(
    name='knv-cli',
    description='Python CLI utility and library for handling data exported from KNV & pcbis.de',
    long_description=long_description(),
    long_description_content_type='text/markdown',
    version=VERSION,
    license='MIT',
    author='Martin Folkers',
    author_email='hello@twobrain.io',
    maintainer='Fundevogel',
    maintainer_email='maschinenraum@fundevogel.de',
    url='https://github.com/Fundevogel/knv-tools',
    project_urls={
        "Source code": "https://github.com/Fundevogel/knv-tools",
        "Issues": "https://github.com/Fundevogel/knv-tools/issues",
    },
    packages=find_packages(),
    install_requires=[
        'click',
        'isbnlib',
        'matplotlib',
        'pandas',
        'pendulum',
        'PyPDF2',
        'xdg',
        'zeep',
    ],
    entry_points='''
        [console_scripts]
        knvcli=knv_cli.cli.cli:cli
    ''',
    python_requires='>=3.6',
)
