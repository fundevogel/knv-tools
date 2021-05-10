# KNV Multitool

## Getting started
Simply run `setup.bash` and you're set!

WIP

```ini
[DEFAULT]
data_dir      = ${XDG_DATA_HOME}/knv-cli  # defaults to /home/$USER/.config/knv-cli
verbose       = off

[import]
import_dir    = ./imports
payment_regex = Download*.CSV
order_regex   = Orders_*.csv
info_regex    = OrdersInfo_*.csv

[export]
export_dir    = ./dist
invoice_file  = invoices.pdf
```

As you can see, many config options refer to the directory from which `knvcli` is being called.

In addition, you might want to provide a list of emails being ignored when creating contact lists using `knvcli ex contacts`. If there's a `blocklist.txt` in your current directory, this is being used (as per global config, see above), or you provide one using the CLI option `-b`. The blocklist should contain one entry per line, like this:

```text
block-me@example.com
pls-me-2@example.com
f!@#ck-u@example.com
```

:copyright: Fundevogel Kinder- und Jugendbuchhandlung
