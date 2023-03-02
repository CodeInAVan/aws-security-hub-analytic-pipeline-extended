#!/usr/bin/env python3
import os
from aws_cdk import core as cdk

# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core

# from stacks.security_hub_collection_stack import SecurityHubCollectionStack
from stacks.security_hub_aggegation_stack import SecurityHubAggregationStack
from stacks.analytic_sink_stack import AnalyticSinkStack
from stacks.quicksight_stack import QuickSightStack
from stacks.quicksight_setup_stack import QuickSightSetupStack
from stacks.athena_stack import AthenaSecurityHubStack
from stacks.athena_setup_stack import AthenaSecurityHubSetupStack

app = core.App()

#  You can get a list of all regions by using these commands
# response = boto3.client('ec2').describe_regions()
# region_names = [r['RegionName'] for r in response['Regions'] if r['OptInStatus'] == 'opt-in-not-required']

analytic_sink_stack = AnalyticSinkStack(app, 'AnalyticSink',
                                        env=cdk.Environment(
                                            region='eu-west-1'
                                        ))

security_hub_aggregation_stack = SecurityHubAggregationStack(app, 'Aggregation',
                            env=cdk.Environment(
                                region='eu-west-1'
                            ),
                            sink_region='eu-west-1')

security_hub_aggregation_stack.add_dependency(analytic_sink_stack)

# setup athena workgroup
athena_security_hub_setup_stack = AthenaSecurityHubSetupStack(app, 'AthenaSecurityHubSetup',
                            env=cdk.Environment(
                                region='eu-west-1'
                            ),
                            sink_region='eu-west-1')
athena_security_hub_setup_stack.add_dependency(security_hub_aggregation_stack)

# setup quicksight iam permissions for service role
quicksight_setup_stack = QuickSightSetupStack(app, 'QuickSightSetup',
                            env=cdk.Environment(
                                region='eu-west-1'
                            ),
                            sink_region='eu-west-1')
quicksight_setup_stack.add_dependency(athena_security_hub_setup_stack)


### THIS SECTION NEEDS TO BE COMMENTED OUT FOR TEH INITIAL DEPLOYMENT OR MOVED TO A NEW CDK APP
### Quicksight doesnt work without data.. code above creates a glue crawler that needs time to run.

# process views in athena/glue and quicksight
files = [
    'security-hub-detail-by-account', 
    'security-hub-detail-flt-cust',
    'security-hub-detail-match-cust'
]

for filename in files:
    athena_security_hub_stack = AthenaSecurityHubStack(app, f'AthenaSecurityHub-{filename}',
                                env=cdk.Environment(
                                    region='eu-west-1'
                                ),
                                sink_region='eu-west-1',
                                view_file=f'./stacks/views/{filename}.json',
                                view_filename=filename)
    athena_security_hub_stack.add_dependency(athena_security_hub_setup_stack)

    quicksight_stack = QuickSightStack(app, f'QuickSight-{filename}',
                                env=cdk.Environment(
                                    region='eu-west-1'
                                ),
                                sink_region='eu-west-1',
                                view_file=f'./stacks/views/{filename}.json',
                                view_filename=filename)
    quicksight_stack.add_dependency(athena_security_hub_stack)
    quicksight_stack.add_dependency(quicksight_setup_stack)

app.synth()
