# KNV Tools

## Getting started
It might be preferable to install `knvcli` inside a virtual environment. This can be done using the `setup.bash` script included in this repository - always check the respective file content before executing the following command, though:

```bash
curl -sf https://raw.githubusercontent.com/fundevogel/knv-tools/main/setup.bash | bash
```

This will

- setup a virtual environment via `virtualenv`
- install the `knvcli` module
- create recommended folders

## Configuration
Adjusting most options to suit your needs is straightforward, global config is stored in `${XDG_CONFIG_HOME}/knv-cli/config` (eg /home/$USER/.config/knv-cli/config), which defaults to this:

```ini
[DEFAULT]
# Enable verbose mode
verbose       = off

# Location of database, eg `/home/$USER/.local/share/knv-cli`
data_dir      = ${XDG_DATA_HOME}/knv-cli

[import]
# Location of files to be processed & imported to database
import_dir    = ./imports

# Regexes for import files
payment_regex = Download*.CSV     # as exported by PayPal™
order_regex   = Orders_*.csv      # as exported by Shopkonfigurator
info_regex    = OrdersInfo_*.csv  # as exported by Shopkonfigurator

[export]
# Location of generated spreadsheets & graphs
export_dir    = ./dist

# Filename of merged invoices when matching PayPal™ payments & invoice numbers
invoice_file  = invoices.pdf
```

As you can see, many config options refer to the directory from which `knvcli` is being called.

In addition, you might want to provide a list of emails being ignored (for example, people opting out of your email marketing campaign) when creating contact lists using `knvcli contacts`. This can be done by providing a `blocklist.txt` in your current directory or using the CLI option `-b`. The blocklist should contain one entry per line, like this:

```text
block-me@example.com
pls-me-2@example.com
f!@#ck-u@example.com
```

**Ideas**
Provide a simple script for backing up contents of `dist` folder, like:

```bash
cd dist || exit

for dir in *
do
    if [ -d "$dir" ]; then
        7z a "$dir".7z "$dir"/* -xr!*.json
    fi
done
```

:copyright: Fundevogel Kinder- und Jugendbuchhandlung
