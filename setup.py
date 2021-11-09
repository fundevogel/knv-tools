import setuptools


# Load README
with open('README.md', 'r', encoding='utf8') as file:
    long_description = file.read()


setuptools.setup(
    name='knv-cli',
    version='0.9.0',
    author='Martin Folkers',
    author_email='hello@twobrain.io',
    maintainer='Fundevogel',
    maintainer_email='maschinenraum@fundevogel.de',
    description='Python CLI utility and library for handling data exported from KNV & pcbis.de',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fundevogel/knv-tools',
    license='MIT',
    project_urls={
        "Issues": "https://github.com/Fundevogel/knv-tools/issues",
    },
    entry_points='''
        [console_scripts]
        knvcli=knv_cli.cli.cli:cli
    ''',
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Office/Business :: Financial :: Accounting",
    ],
    packages=setuptools.find_packages(),
    install_requires=[
        'click',
        'isbnlib',
        'matplotlib',
        'pandas',
        'pendulum',
        'PyPDF2',
        'reportlab',
        'xdg',
        'zeep',
    ],
    python_requires='>=3.6',
)
