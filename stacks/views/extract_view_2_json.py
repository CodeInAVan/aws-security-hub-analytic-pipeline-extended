import os
import json
import base64

view="security-hub-detail-match-cust"
region="eu-west-1"
database="security_hub_database"

tabledef_raw = os.popen(f'aws glue get-table --database-name={database} --region={region} --name {view}')
tabledef_json = json.loads(tabledef_raw.read())['Table']
test=tabledef_json['ViewOriginalText'][16:len(tabledef_json['ViewOriginalText'])-3]

decodedBytes = base64.b64decode(test)
decodedStr = decodedBytes.decode("ascii") 
json_str=json.loads(decodedStr)

gluedata=json_str
#print(type(gluedata))

json_data = {}
json_data["name"]=view
json_data["gluedata"]=gluedata
json_data["gluedata"]["owner"]="<SET ME IN CODE>"
json_data["quicksight_input_columns"]=tabledef_json["StorageDescriptor"]["Columns"]

mylist=[]

for d in tabledef_json["StorageDescriptor"]["Columns"]:
    #myset = ""
    #print(d)
    newd=dict((k.lower(), v) for k,v in d.items())
    #print(newd)
    mylist.append(newd)

#print(mylist)
json_data["column_data"]=mylist

mylist=[]
for d in tabledef_json["StorageDescriptor"]["Columns"]:

    newd=dict((
        k.lower(),
        ("INTEGER" if v == "bigint" else v.upper()) if (v == "string" or v == "bigint") else v.lower())   
        for k,v in d.items())

    #print(newd)
    mylist.append(newd)

print(mylist)
json_data["quicksight_input_columns"]=mylist

#print(mylist)


# new_data = {key.lower():value for key, value in data.items()}
# json_data["column_data"]=new_data

json_object=json.dumps(json_data, indent=4)
#print(json_object)
# Object.keys(json_object).map(key => {
#   if(key.toLowerCase() != key){
#     json_object[key.toLowerCase()] = json_object[key];
#     delete json_object[key];
#   }
# });


view_filename=view.replace("_","-")
# Writing to sample.json
with open(f"{view_filename}.json", "w") as outfile:
    outfile.write(json_object)



    







