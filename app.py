#!/usr/bin/env python3
import os
import aws_cdk as cdk

from lex_openai.lex_openai_stack import LexOpenAiStack

# Variables
DOCUMENT_DIR = os.path.join(os.path.dirname(__file__), 'documents')
OPENAI_KEY_PATH = '/openai/api_key'

# Stack
app = cdk.App()
LexOpenAiStack(app, 'LexOpenAiStack',
    document_dir=DOCUMENT_DIR,
    openai_key_path=OPENAI_KEY_PATH,
    env=cdk.Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION'),
    ),
)

app.synth()
