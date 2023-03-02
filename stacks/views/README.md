### VIEW CREATION

json file contains the presto and hive versions of the data structure (borrowed from terraform examples!)

data is used to create glue table based on view SQL

note the SQL must be a single line and have escaped quotes e.g. \" not "

### helper script

extract_view_2_json.py - use this to extract a manually created view into json for automation

edit it to set view name and then run 

```bash
$ python3 extract_view_2_json.py
```

### Hive to Presto type conversion

Since complex types can be arbitrarily nested you need a proper parser to safely convert between Hive and Presto type names, [regular expressions aren't sufficient](https://stackoverflow.com/questions/546433/regular-expression-to-match-balanced-parentheses). Instead, here's a table you can use to convert between the two:

Hive type | Presto type
---|---
`string` | `varchar`
`array<E>` | `array(E)`
`map<K, V>` | `map(K, V)`
`struct<F1:T1, F2:T2>` | `row(F1 T1, F2 T2)`

All other types have the same name in Hive and Presto (if you find an exception please open a PR with a correction).




'''

{
  "name": "view_name",
  "gluedata": {
    "catalog": "awsdatacatalog",
    "columns": [
      {
        "name": "col1",
        "type": "varchar"
      },
      {
        "name": "col2",
        "type": "bigint"
      },
    
    ],
    "originalSql": "SELECT statement with \"quotes\" escaped"
  },
  "column_data": [
    {
      "name": "col1",
      "type": "string"
    },
    {
      "name": "col2",
      "type": "bigint"
    },
   
  ],
  "quicksight_input_columns": [
    {
      "name": "col1",
      "type": "STRING"
    },
    {
      "name": "col2",
      "type": "INTEGER"
    }
  ]
}
'''