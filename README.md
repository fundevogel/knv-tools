# KNV Tools

## Getting started
It might be preferable to install `knvcli` inside a virtual environment. This can be done using the `setup.bash` script included in this repository - always check the respective file content before executing the following command, though:

```bash
curl -sf https://raw.githubusercontent.com/fundevogel/knv-tools/main/setup.bash | bash
```

This will

- setup a virtual environment via [`virtualenv`](https://virtualenv.pypa.io)
- install the `knvcli` module
- create recommended folders

After that, simply activate the virtual environment with `source .env/bin/activate` and you're good to go.

Alternatively, you may install it globally, using [`pip`](https://pip.pypa.io):

```bash
pip install git+https://github.com/Fundevogel/knv-tools.git
```

## Configuration
Adjusting most options to suit your needs is straightforward, global config is stored in `${XDG_CONFIG_HOME}/knv-cli/config` (following [XDG specifications](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)) and defaults to this:

```ini
[DEFAULT]
verbose = off  # Enable verbose mode

[directories]
data_dir = ~/.local/share/knv-cli  # database directory
import_dir = ./imports             # files to be processed & imported to database
export_dir = ./dist                # generated spreadsheets & graphs

# Regexes for import files
[regexes]
payment_regex = Download*.CSV  # as exported by PayPal™
order_regex = Orders_*.csv     # as exported by Shopkonfigurator
info_regex = OrdersInfo_*.csv  # as exported by Shopkonfigurator
```

As you can see, many config options refer to the directory from which `knvcli` is being called.

In addition, you might want to provide a list of emails being ignored (for example, people opting out of your email marketing campaign) when creating contact lists using `knvcli contacts`. This can be done by providing a `blocklist.txt` in your current directory or using the CLI option `-b`. The blocklist should contain one entry per line, like this:

```text
block-me@example.com
pls-me-2@example.com
f!@#ck-u@example.com
```

## Roadmap

In the future, the following features & improvements are planned:

- ~~bar charts for sales rankings~~
- export functions for `Database`
- preparing tax declarations using automation
- .. and much more

:copyright: Fundevogel Kinder- und Jugendbuchhandlung
