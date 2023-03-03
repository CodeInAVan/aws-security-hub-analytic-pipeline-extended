### VIEW CREATION

Process :
- create view manually in athena
- edit python file to the view you want and set local creds so you can access the view 
- run script, output is .json that contains view defenition in various formats for the cdk to consume

### helper script

extract_view_2_json.py - use this to extract a manually created view into json for automation

edit it to set view name and then run 

```bash
$ python3 extract_view_2_json.py
```

script runs

```bash
aws glue get-table --database-name={database} --region={region} --name {view}
```

resulting .json file contains the presto and hive versions of the data structure (borrowed from terraform examples!) for glue and modified versions for quicksight.

Data is used to create glue table based on view SQL, please note the script also tries to convert presto types to the upper case types used in quicksight datasets (see quicksight_input_columns), it only handles varchar and bigint types, you will have to adjust it or manually fix any other types in the json.

Note the originalSql must be a single line and have escaped quotes e.g. 

```
\" 

not "
```

```
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
```