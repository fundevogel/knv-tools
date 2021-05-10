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

:copyright: Fundevogel Kinder- und Jugendbuchhandlung
