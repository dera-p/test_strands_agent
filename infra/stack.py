from aws_cdk import (
    Stack,
    CfnOutput,
    aws_iam as iam,
    aws_s3 as s3,
    RemovalPolicy,
)
from aws_cdk import aws_bedrockagentcore as agentcore
from constructs import Construct
import os

class StrandsAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get account and region for IAM policies
        region = Stack.of(self).region
        account_id = Stack.of(self).account

        # 0. Create S3 Bucket for PPTX output
        output_bucket = s3.Bucket(
            self, "PPTXOutputBucket",
            bucket_name=f"strands-pptx-output-{account_id}",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,  # For development
            auto_delete_objects=True,  # For development
        )

        # 1. Create IAM Role for AgentCore Runtime
        runtime_role = iam.Role(
            self, "AgentCoreRuntimeRole",
            role_name="StrandsAgentCoreRuntimeRole",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Execution role for Bedrock AgentCore runtime hosting Strands PowerPoint agent"
        )

        # 2. Add required IAM policies for AgentCore
        
        # CloudWatch Logs
        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogsAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*",
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*",
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:*",
                    f"arn:aws:logs:{region}:{account_id}:log-group:*",
                ],
            )
        )

        # X-Ray Telemetry
        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="XRayTelemetry",
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                resources=["*"],
            )
        )

        # Bedrock Model Invocation (for Strands Agent reasoning)
        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockModelInvocation",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/*",
                    f"arn:aws:bedrock:{region}:{account_id}:*",
                ],
            )
        )

        # S3 Access for file uploads
        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3FileUpload",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:PutObjectAcl",
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    output_bucket.bucket_arn,
                    output_bucket.arn_for_objects("*")
                ],
            )
        )

        # CloudWatch Metrics
        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchMetrics",
                effect=iam.Effect.ALLOW,
                actions=["cloudwatch:PutMetricData"],
                resources=["*"],
                conditions={
                    "StringEquals": {
                        "cloudwatch:namespace": "bedrock-agentcore",
                    },
                },
            )
        )

        # Workload Access Token (if needed)
        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="AgentWorkloadAccessToken",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock-agentcore:GetWorkloadAccessToken",
                    "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
                    "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
                ],
                resources=[
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default",
                    f"arn:aws:bedrock-agentcore:{region}:{account_id}:workload-identity-directory/default/workload-identity/*",
                ],
            )
        )

        # 3. Create ECR Docker Image Asset
        from aws_cdk import aws_ecr_assets as ecr_assets

        docker_image_asset = ecr_assets.DockerImageAsset(
            self, "StrandsAgentDockerImage",
            directory=".",  # Root directory containing Dockerfile.agentcore
            file="Dockerfile.agentcore",
            platform=ecr_assets.Platform.LINUX_ARM64,
            exclude=["cdk.out", ".git", "node_modules", "__pycache__"],
        )

        # Add ECR permissions to runtime role
        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="ECRImageAccess",
                effect=iam.Effect.ALLOW,
                actions=["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
                resources=[
                    f"arn:aws:ecr:{region}:{account_id}:repository/{docker_image_asset.repository.repository_name}",
                ],
            )
        )

        runtime_role.add_to_policy(
            iam.PolicyStatement(
                sid="ECRAuthToken",
                effect=iam.Effect.ALLOW,
                actions=["ecr:GetAuthorizationToken"],
                resources=["*"],
            )
        )

        # 4. Create AgentCore Runtime using CfnRuntime (L1 construct)
        cfn_runtime = agentcore.CfnRuntime(
            self, "StrandsPowerPointRuntime",
            agent_runtime_name="StrandsPPTXAgent",
            agent_runtime_artifact=agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=docker_image_asset.image_uri
                )
            ),
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC"
            ),
            role_arn=runtime_role.role_arn,
            protocol_configuration="HTTP",
        )

        cfn_runtime.node.add_dependency(runtime_role)
        cfn_runtime.node.add_dependency(output_bucket)

        # 5. Output the Runtime ARN
        CfnOutput(self, "RuntimeArn", value=cfn_runtime.attr_agent_runtime_arn)
        CfnOutput(self, "RuntimeName", value="StrandsPPTXAgent")
        CfnOutput(self, "OutputBucketName", value=output_bucket.bucket_name)
