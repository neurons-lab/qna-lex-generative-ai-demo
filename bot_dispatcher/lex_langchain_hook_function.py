"""
Lambda that acts as the fulfillment hook for a Lex bot on AWS Solution
"""
from dispatchers.LexV2SMOpenAILangchainDispatcher import LexV2SMOpenAILangchainDispatcher
from dispatchers import utils
import logging


logger = utils.get_logger(__name__)
logger.setLevel(logging.DEBUG)


def dispatch_openai(request):
    """Summary

    Args:
        request (dict): Lambda event containing an user's input chat message and context (historical conversation)
        Uses the LexV2 sessions API to manage past inputs https://docs.aws.amazon.com/lexv2/latest/dg/using-sessions.html

    Returns:
        dict: Description
    """
    openai_dispatcher = LexV2SMOpenAILangchainDispatcher(request)
    return openai_dispatcher.dispatch_intent()


def lambda_handler(event, context):
    print('event:', event)
    if 'sessionState' in event:
        if 'intent' in event['sessionState']:
            if 'name' in event['sessionState']['intent']:
                if event['sessionState']['intent']['name'] == 'FallbackIntent':
                    return dispatch_openai(event)
    else:
        raise Exception('No sessionState in event')
