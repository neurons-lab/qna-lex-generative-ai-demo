from aws_cdk import (
    RemovalPolicy,
    Duration,
    Stack,
    CfnOutput,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_kendra as kendra,
    aws_lex as lex,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _lambda_python,
    aws_logs as logs,
)
from constructs import Construct


class LexOpenAiStack(Stack):
    """Main"""
    def __init__(self,
                 scope: Construct,
                 construct_id: str,
                 document_dir: str = './documents',
                 openai_key_path: str = '/openai/api_key',
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for documents
        document_bucket = s3.Bucket(
            self, 'HandbookDocKendraBucket',
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True)

        # Upload documents to S3 bucket
        s3deploy.BucketDeployment(
            self, 'HandbookKendraBucketDeployment',
            sources=[s3deploy.Source.asset(document_dir)],
            destination_bucket=document_bucket)

        # Kendra role
        kendra_role = iam.Role(
            self, 'HandbookKendraIndexRole',
            assumed_by=iam.ServicePrincipal('kendra.amazonaws.com'),
            inline_policies={
                'kendra-policy': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                's3:GetObject',
                                's3:ListBucket',
                                'cloudwatch:PutMetricData',
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:DescribeLogGroups',
                                'logs:DescribeLogStreams',
                                'logs:PutLogEvents',
                            ],
                            resources=[
                                document_bucket.bucket_arn,
                                f'{document_bucket.bucket_arn}/*',
                                f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/kendra/*',
                            ]
                        ),
                    ]
                )
            }
        )

        # Kendra index over document bucket
        kendra_index = kendra.CfnIndex(
            self, 'HandbookKendraIndex',
            name='HandbookKendraIndex',
            edition='DEVELOPER_EDITION',
            description='Handbook Kendra Index',
            role_arn=kendra_role.role_arn,
        )

        # Kendra data source
        kendra.CfnDataSource(
            self, 'HandbookKendraDataSource',
            name='HandbookKendraDataSource',
            index_id=kendra_index.attr_id,
            type='S3',
            role_arn=kendra_role.role_arn,
            data_source_configuration=kendra.CfnDataSource.DataSourceConfigurationProperty(
                s3_configuration=kendra.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_name=document_bucket.bucket_name,
                )
            ),
        )

        # Output
        CfnOutput(
            self, 'KendraIndexId',
            value=kendra_index.attr_id,
            description='Kendra Index ID')

        # Fallback lambda
        fallback_lambda_role = iam.Role(
            self, 'FallbackLambdaRole',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('lambda.amazonaws.com'),
                iam.ServicePrincipal('lex.amazonaws.com'),
                iam.ServicePrincipal('lexv2.amazonaws.com'),
            ),
            # Basic lambda execution policy
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
            ],
            inline_policies={
                'lambda-policy': iam.PolicyDocument(
                    statements=[
                        # Kendra query permissions
                        iam.PolicyStatement(
                            actions=[
                                'kendra:Query',
                            ],
                            resources=['*']
                        ),
                        # CloudWatch logs permissions
                        iam.PolicyStatement(
                            actions=[
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources=['*']
                        ),
                        # SSM get parameter permissions
                        iam.PolicyStatement(
                            actions=[
                                'ssm:GetParameter',
                            ],
                            resources=['*']
                        ),
                    ]
                )
            }
        )

        # Lambda function definition
        fallback_lex_lambda = _lambda_python.PythonFunction(
            self, 'LexOpenAIBotLambdaHook',
            description='QnA Bot OpenAI Lambda Hook',
            entry='./bot_dispatcher',
            index='lex_langchain_hook_function.py',
            handler='lambda_handler',
            environment={
                'API_KEY_PARAMETER_PATH': openai_key_path,
                'KENDRA_INDEX_ID': kendra_index.attr_id,
            },
            runtime=_lambda.Runtime.PYTHON_3_9,
            role=fallback_lambda_role,
            timeout=Duration.seconds(900),
            memory_size=1024,
            log_retention=logs.RetentionDays.ONE_MONTH)

        # Allow Lex Bot to invoke the Lambda function
        _lambda.CfnPermission(
            self, 'LexOpenAIBotLambdaHookPermission',
            action='lambda:InvokeFunction',
            principal='lex.amazonaws.com',
            function_name=fallback_lex_lambda.function_name,
            source_arn=f'arn:aws:lex:{self.region}:{self.account}:bot-alias/*',
            source_account=self.account)

        # Output
        CfnOutput(
            self, 'LexLambdaFunctionName',
            value=fallback_lex_lambda.function_name,
            description='Fallback Lex Lambda Function Name')

        # Lex bot role
        lex_role = iam.Role(
            self, 'LexOpenAIBotRole',
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal('lex.amazonaws.com'),
                iam.ServicePrincipal('lexv2.amazonaws.com'),
            ),
            inline_policies={
                'lex-policy': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                'polly:SynthesizeSpeech',
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents',
                            ],
                            resources=['*']
                        ),
                    ]
                )
            }
        )

        # Lex bot
        lex_bot = lex.CfnBot(
            self, 'LexOpenAIBot',
            name='LexOpenAIBot',
            data_privacy={
                'ChildDirected': False,
            },
            idle_session_ttl_in_seconds=300,
            role_arn=lex_role.role_arn,
            auto_build_bot_locales=False,
            bot_locales=[
                lex.CfnBot.BotLocaleProperty(
                    intents=[
                        lex.CfnBot.IntentProperty(
                            intent_closing_setting=lex.CfnBot.IntentClosingSettingProperty(
                                closing_response=lex.CfnBot.ResponseSpecificationProperty(
                                    message_groups_list=[
                                        lex.CfnBot.MessageGroupProperty(
                                            message=lex.CfnBot.MessageProperty(
                                                plain_text_message=lex.CfnBot.PlainTextMessageProperty(
                                                    value="Hello I am a sample Lex Bot that calls a OpenAI model using langchain"
                                                )
                                            )
                                        )
                                    ]
                                )
                            ),
                            name="DescribeLexBot",
                            sample_utterances=[
                                lex.CfnBot.SampleUtteranceProperty(
                                    utterance="Describe bot"
                                )
                            ]
                        ),
                        lex.CfnBot.IntentProperty(
                            description="Fallback intent which calls OpenAI model using langchain",
                            fulfillment_code_hook=lex.CfnBot.FulfillmentCodeHookSettingProperty(enabled=True),
                            dialog_code_hook=lex.CfnBot.DialogCodeHookSettingProperty(enabled=False),
                            name="FallbackIntent",
                            parent_intent_signature="AMAZON.FallbackIntent"
                        )
                    ],
                    locale_id="en_US",
                    nlu_confidence_threshold=0.4
                ),
            ],
            test_bot_alias_settings=lex.CfnBot.TestBotAliasSettingsProperty(
                bot_alias_locale_settings=[
                    lex.CfnBot.BotAliasLocaleSettingsItemProperty(
                        bot_alias_locale_setting=lex.CfnBot.BotAliasLocaleSettingsProperty(
                            enabled=True,
                            code_hook_specification=lex.CfnBot.CodeHookSpecificationProperty(
                                lambda_code_hook=lex.CfnBot.LambdaCodeHookProperty(
                                    code_hook_interface_version="1.0",
                                    lambda_arn=fallback_lex_lambda.function_arn,
                                )
                            )
                        ),
                        locale_id="en_US",
                    )
                ],
            )
        )

        # Output
        CfnOutput(
            self, 'LexBotName',
            value=lex_bot.name)
