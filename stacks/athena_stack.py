from os import path
from aws_cdk import (
    core as cdk,
    aws_iam as iam,
    aws_glue as glue,
    aws_lambda as lmb,
    aws_lambda_python as lambda_python,
    aws_ssm as ssm,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications
)
import aws_cdk.aws_athena as athena
import aws_cdk.aws_quicksight as quicksight
import base64
import json

from custom_constructs.ssm_stored_parameter import SSMStoredParameter

class AthenaSecurityHubStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, sink_region: str, view_file: str, view_filename: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
      
        # create athena view from file
        with open(view_file) as f:
            d = json.load(f)
        
        # update owner in view json
        d["gluedata"]["owner"] = self.account
        
        # read the presto data for the view, this needs to be encoded in the table created in glue
        json_data = d["gluedata"]


        # json to string
        newjsonData = json.dumps(json_data)

        #base64 encode the data from str to binary to base64
        encoded = base64.b64encode(newjsonData.encode('utf-8'))

        column_data = d["column_data"]

        athena_database_name = "security_hub_database"

        # read view name from file
        view_name = d["name"]

        # tell glue this is a presto view
        parameters = {'presto_view': 'true'}

        # result is bytes type, base64 encoded string, needs to be str type for presto (see below)
        view_original_text = f'/* Presto View: {encoded.decode("ascii")} */'
        
        # aws account is catalog_id
        catalog_id = self.account

        newtable = glue.CfnTable(self, "MyCfnTable",
            catalog_id=catalog_id,
            database_name=athena_database_name,
            table_input=glue.CfnTable.TableInputProperty(
                description="description",
                name=view_name,    
                parameters=parameters,
                storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                    serde_info=glue.CfnTable.SerdeInfoProperty(
                        name="-",
                        serialization_library="-"
                    ),
                    columns=column_data,
                ),
            view_original_text = view_original_text,
            table_type = "VIRTUAL_VIEW",
            ),
        )

