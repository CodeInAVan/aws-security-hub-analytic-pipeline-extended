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
import json
import aws_cdk.aws_s3_deployment as s3deploy

class AnalyticSinkStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        destination_prefix = 'Findings'
        this_dir = path.dirname(__file__)

        self.__bucket = s3.Bucket(self, 'Bucket',
                                  auto_delete_objects=True,
                                  removal_policy=cdk.RemovalPolicy.DESTROY,
                                  encryption=s3.BucketEncryption.S3_MANAGED
                                  )

 

        self.__query_result_bucket = s3.Bucket(self, 'QueryResultBucket',
                                             removal_policy=cdk.RemovalPolicy.RETAIN,
                                             encryption=s3.BucketEncryption.S3_MANAGED)


        ## add policy for quicksight to bucket
        bucket_policy=iam.PolicyStatement(
            actions=["s3:Get*", "s3:List*","s3:PutObject"],
            resources=[
                self.__bucket.arn_for_objects("*"), 
                self.__bucket.bucket_arn,
            ],
            principals=[iam.ArnPrincipal("arn:aws:iam::" + self.account + ":role/service-role/aws-quicksight-service-role-v0")]
        )

        self.__bucket.add_to_resource_policy(bucket_policy);

        ## end add policy for quicksight to bucket

        ## upload control lists to bucket
        s3deploy.BucketDeployment(self, "DeployButIncludeSpecificFiles",
            sources=[s3deploy.Source.asset("./stacks/controllists")],
            destination_bucket=self.__bucket,
            include=["*.csv"],
            destination_key_prefix="controllists"
            )
        ## end upload control lists to bucket

        # Make bucket accessible via other stacks in other Regions
        ssm.StringParameter(self, 'BucketParameter',
                            parameter_name='/AnalyticSinkStack/BucketName',
                            string_value=self.__bucket.bucket_name)
        ssm.StringParameter(self, 'BucketArn',
                            parameter_name='/AnalyticSinkStack/BucketArn',
                            string_value=self.__bucket.bucket_arn)

        # Transforms Findings so that keys are consumable by Athena
        transform_findings = lambda_python.PythonFunction(self, 'TransformFindings',
                                                          entry=path.join(this_dir,
                                                                          '../assets/lambdas/transform_findings'),
                                                          handler='handler',
                                                          runtime=lmb.Runtime.PYTHON_3_8,
                                                          timeout=cdk.Duration.seconds(300),
                                                          environment={
                                                              'bucket_name': self.__bucket.bucket_name,
                                                              'destination_prefix': destination_prefix
                                                          })

        self.__bucket.grant_read_write(transform_findings)

        # added /raw here to stop lambda reading its own results!
        self.__bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3_notifications.LambdaDestination(transform_findings),s3.NotificationKeyFilter(
                prefix="raw/",
            ),
        )

        role = iam.Role(self, 'CrawlerRole',
                        assumed_by=iam.ServicePrincipal('glue.amazonaws.com'))

        

        self.__bucket.grant_read(role)
        
        role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                's3:GetBucketLocation',
                's3:ListBucket',
                's3:ListAllMyBuckets',
                's3:GetBucketAcl'
            ],
            resources=[f'{self.__bucket.bucket_arn}*']
        ))
        # Glue Permissions
        role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'glue:*',
                'iam:ListRolePolicies',
                'iam:GetRole',
                'iam:GetRolePolicy'
            ],
            resources=['*']
        ))
        role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                's3:GetObject'
            ],
            resources=[
                'arn:aws:s3:::crawler-public*',
                'arn:aws:s3:::aws-glue-*'
            ]
        ))
        role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents'
            ],
            resources=['arn:aws:logs:*:*:/aws-glue/*']
        ))

        database = glue.Database(self, 'SecurityHubDatabase',
                                 database_name='security_hub_database')

        raw_crawler_configuration = {
            'Version': 1.0,
            # 'CrawlerOutput': {
            #     'Partitions': {'AddOrUpdateBehavior': 'InheritFromTable'}
            # },
            'Grouping': {
                'TableGroupingPolicy': 'CombineCompatibleSchemas'}
        }

        glue.CfnCrawler(self, 'SecurityHubCrawler',
                        role=role.role_arn,
                        database_name=database.database_name,
                        schedule=glue.CfnCrawler.ScheduleProperty(
                            schedule_expression='cron(0 0/1 * * ? *)'
                        ),
                        targets=glue.CfnCrawler.TargetsProperty(
                            s3_targets=[glue.CfnCrawler.S3TargetProperty(
                                path=f's3://{self.__bucket.bucket_name}/{destination_prefix}/securityhub'
                            )]
                        ),
                        table_prefix='security-hub-crawled-securityhub-',
                        name='SecurityHubCrawler',
                        configuration=json.dumps(raw_crawler_configuration))

        glue.CfnCrawler(self, 'GuardDutyCrawler',
                        role=role.role_arn,
                        database_name=database.database_name,
                        schedule=glue.CfnCrawler.ScheduleProperty(
                            schedule_expression='cron(0 0/1 * * ? *)'
                        ),
                        targets=glue.CfnCrawler.TargetsProperty(
                            s3_targets=[glue.CfnCrawler.S3TargetProperty(
                                path=f's3://{self.__bucket.bucket_name}/{destination_prefix}/guardduty'
                            )]
                        ),
                        table_prefix='security-hub-crawled-guardduty-',
                        name='GuardDutyCrawler',
                        configuration=json.dumps(raw_crawler_configuration))

        glue.CfnCrawler(self, 'SecurityHubControls',
                        role=role.role_arn,
                        database_name=database.database_name,
                        schedule=glue.CfnCrawler.ScheduleProperty(
                            schedule_expression='cron(0 8 * * ? *)'
                        ),
                        targets=glue.CfnCrawler.TargetsProperty(
                            s3_targets=[glue.CfnCrawler.S3TargetProperty(
                                path=f's3://{self.__bucket.bucket_name}/controllists/security_hub'
                            )]
                        ),
                        table_prefix='security-hub-controls-',
                        name='SecurityHubControls')
                        # configuration=json.dumps(raw_crawler_configuration))


        glue.CfnCrawler(self, 'ConfigControlSources',
                        role=role.role_arn,
                        database_name=database.database_name,
                        schedule=glue.CfnCrawler.ScheduleProperty(
                            schedule_expression='cron(0 8 * * ? *)'
                        ),
                        targets=glue.CfnCrawler.TargetsProperty(
                            s3_targets=[glue.CfnCrawler.S3TargetProperty(
                                path=f's3://{self.__bucket.bucket_name}/controllists/config'
                            )]
                        ),
                        table_prefix='security-hub-config-',
                        name='ConfigControlSources')
                        # configuration=json.dumps(raw_crawler_configuration))
    @property
    def target_bucket(self) -> s3.Bucket:
        return self.__bucket

    @property
    def query_result_bucket(self) -> s3.Bucket:
        return self.__query_result_bucket