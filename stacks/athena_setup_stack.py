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

class AthenaSecurityHubSetupStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, sink_region: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        
        sink_bucket_name = SSMStoredParameter(self, 'BucketName',
                                              parameter_name='/AnalyticSinkStack/BucketName',
                                              region=sink_region).value_as_a_string
        sink_bucket_arn = SSMStoredParameter(self, 'BucketArn',
                                             parameter_name='/AnalyticSinkStack/BucketArn',
                                             region=sink_region).value_as_a_string




        # create workgroup
        athena_output_prefix = "output"
        athena_workgroup_name = f"security_hub"
        athena_workgroup = athena.CfnWorkGroup(
            self,
            "Workgroup",
            name=athena_workgroup_name,
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{sink_bucket_name}/{athena_output_prefix}/",
                    encryption_configuration=athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_S3"
                    ),
                ),
                engine_version=athena.CfnWorkGroup.EngineVersionProperty(
                    effective_engine_version="Athena engine version 3",
                    selected_engine_version="Athena engine version 3"
                ),
            ),
            recursive_delete_option=True,
            
        )

        