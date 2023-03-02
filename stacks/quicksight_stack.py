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
import json

from custom_constructs.ssm_stored_parameter import SSMStoredParameter

class QuickSightStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, sink_region: str, view_file: str, view_filename: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        ## TODO CREATE THIS GROUP!!
        qs_principal_arn="arn:aws:quicksight:" + self.region + ":" + self.account + ":group/default/securityhub"
        
        ## user perms example
        # qs_data_source_permissions = [
        #     quicksight.CfnDataSource.ResourcePermissionProperty(
        #         principal=qs_principal_arn,
        #         actions=[
        #             "quicksight:DescribeDataSource",
        #             "quicksight:DescribeDataSourcePermissions",
        #             "quicksight:PassDataSource",
        #         ],
        #     ),
        # ]
        
       ## admin perms example
        qs_data_source_permissions = [
            quicksight.CfnDataSource.ResourcePermissionProperty(
                principal=qs_principal_arn,
                actions=[
                    "quicksight:UpdateDataSourcePermissions", 
                    "quicksight:DescribeDataSourcePermissions", 
                    "quicksight:PassDataSource", 
                    "quicksight:DescribeDataSource", 
                    "quicksight:DeleteDataSource", 
                    "quicksight:UpdateDataSource",
                ],
            ),
        ]

        ## user perms example
        # qs_dataset_permissions = [
        #     quicksight.CfnDataSet.ResourcePermissionProperty(
        #         principal=qs_principal_arn,
        #         actions=[
        #             "quicksight:DescribeDataSet",
        #             "quicksight:DescribeDataSetPermissions",
        #             "quicksight:PassDataSet",
        #             "quicksight:DescribeIngestion",
        #             "quicksight:ListIngestions",
        #         ],
        #     )
        # ]

        
        ## admin perms example
        qs_dataset_permissions = [
            quicksight.CfnDataSet.ResourcePermissionProperty(
                principal=qs_principal_arn,
                actions=[
                    "quicksight:PassDataSet", 
                    "quicksight:DescribeIngestion", 
                    "quicksight:CreateIngestion", 
                    "quicksight:UpdateDataSet", 
                    "quicksight:DeleteDataSet", 
                    "quicksight:DescribeDataSet", 
                    "quicksight:CancelIngestion", 
                    "quicksight:DescribeDataSetPermissions", 
                    "quicksight:ListIngestions", 
                    "quicksight:UpdateDataSetPermissions",
                ],
            )
        ]

        ## ATHENA DATA SOURCE
        qs_athena_data_source_name = f'security_hub_test-{view_filename}'
        athena_workgroup_name="security_hub"

        qs_athena_data_source = quicksight.CfnDataSource(
            self,
            "AthenaDataSource",
            name=qs_athena_data_source_name,
            data_source_parameters=quicksight.CfnDataSource.DataSourceParametersProperty(
                athena_parameters=quicksight.CfnDataSource.AthenaParametersProperty(
                    work_group=athena_workgroup_name
                )
            ),
            type="ATHENA",
            aws_account_id=self.account,
            data_source_id=qs_athena_data_source_name,
            ssl_properties=quicksight.CfnDataSource.SslPropertiesProperty(
                disable_ssl=False
            ),
            permissions=qs_data_source_permissions,
        )

        #qs_athena_data_source.add_depends_on(qs_managed_policy)

        # ATHENA DATASET

        with open(view_file) as f:
            d = json.load(f)
            #print(d)
        quicksight_input_columns = d["quicksight_input_columns"]
        quicksight_view_name = d["name"]

        athena_database_name="security_hub_database"
        qs_athena_dataset_physical_table = (
            quicksight.CfnDataSet.PhysicalTableProperty(
                relational_table=quicksight.CfnDataSet.RelationalTableProperty(
                    data_source_arn=qs_athena_data_source.attr_arn,
                    input_columns=quicksight_input_columns,
                    catalog="AWSDataCatalog",
                    schema=athena_database_name,
                    name=quicksight_view_name,
                )
            )
        )


        qs_import_mode = "SPICE"
        qs_dataset_name = f'security_hub_database_view_{view_filename}-ds'
        qs_athena_dataset_raw = quicksight.CfnDataSet(
            self,
            f"Dataset-athena-securityhub-{view_filename}",
            import_mode=qs_import_mode,
            name=qs_dataset_name,
            aws_account_id=self.account,
            data_set_id=qs_dataset_name,
            physical_table_map={
                f'athena-security-hub-table-{view_filename}': qs_athena_dataset_physical_table
            },
            permissions=qs_dataset_permissions,
        )
        qs_athena_dataset_raw.add_depends_on(qs_athena_data_source)