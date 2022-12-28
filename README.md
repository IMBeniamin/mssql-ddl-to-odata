# mssql-ddl-to-odata
Convert MSSQL DDL (decently) formatted syntax to a json that is parseable and usable by and odata api
Usage:
```
positional arguments:
  input_file   path to input file
  output_file  path to output file

options:
  -h, --help   show this help message and exit
  -P, --print
  ```
Example:
```
py ./mssql_to_odata_json.py --print source.sql output.json
```
