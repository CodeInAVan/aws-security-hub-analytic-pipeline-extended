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

class QuickSightSetupStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, sink_region: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        
        
        sink_bucket_name = SSMStoredParameter(self, 'BucketName',
                                              parameter_name='/AnalyticSinkStack/BucketName',
                                              region=sink_region).value_as_a_string
        sink_bucket_arn = SSMStoredParameter(self, 'BucketArn',
                                             parameter_name='/AnalyticSinkStack/BucketArn',
                                             region=sink_region).value_as_a_string

        qs_service_role_names = [
            "aws-quicksight-service-role-v0",
            # "aws-quicksight-s3-consumers-role-v0",
        ]

        athena_output_prefix = "output"
        qs_managed_policy = iam.CfnManagedPolicy(
            self,
            "QuickSightPolicy",
            managed_policy_name="QuickSightDemoAthenaS3Policy",
            policy_document=dict(
                Statement=[
                    dict(
                        Action=["s3:ListAllMyBuckets"],
                        Effect="Allow",
                        Resource=["arn:aws:s3:::*"],
                    ),
                    dict(
                        Action=["s3:ListBucket"],
                        Effect="Allow",
                        Resource=[
                            f"arn:aws:s3:::{sink_bucket_name}",
                        ],
                    ),
                    dict(
                        Action=[
                            "s3:GetObject",
                            "s3:List*",
                        ],
                        Effect="Allow",
                        Resource=[
                            f"arn:aws:s3:::{sink_bucket_name}/Findings/*",
                        ],
                    ),
                    dict(
                        Action=[
                            "s3:GetObject",
                            "s3:List*",
                            "s3:AbortMultipartUpload",
                            "s3:PutObject",
                        ],
                        Effect="Allow",
                        Resource=[
                            f"arn:aws:s3:::{sink_bucket_name}/{athena_output_prefix}/*",
                        ],
                    ),
                ],
                Version="2012-10-17",
            ),
            roles=qs_service_role_names,
        )

        