import os
import sys
sys.path.append(os.path.dirname(__file__))

import re
import json

from ai_predict_through_doc import AIPredictThroughDoc


class OpenAILangchainBot():
    """Create a langchain.ConversationChain using a Sagemaker endpoint as the LLM

    Attributes:
        chain (langchain.ConversationChain): 
            Langchain chain that invokes the Sagemaker endpoint hosting an LLM
    """

    def __init__(self, lex_conv_history=""):
        """Create a SagemakerLangchainBot client
        
        Args:
            lex_conv_history (str, optional): Lex convo history from LexV2 sessions API. 
                Empty string for no history (first chat)
        """

        self.qa_module = AIPredictThroughDoc()
        self.chat_history = json.loads(lex_conv_history) if lex_conv_history else {}

    def call_llm(self, user_input) -> str:
        """Call the Sagemaker endpoint hosting the LLM by calling ConversationChain.predict()
        
        Args:
            user_input (str): User chat input
        
        Returns:
            str: Sagemaker response to display as chat output
        """

        # Converting "Ai:Human:" to Tuples for request
        chat_history = self.chat_history['chat_history'] if self.chat_history else ''
        chat_array = list(map(lambda line: re.sub(r'(^AI:\s*)|(^Human:\s*)', '', line), chat_history.split('\n')[1:-1]))
        chat_tuples = list(zip(chat_array[0::2], chat_array[1::2]))

        qa_chat_history = chat_tuples if self.chat_history else []
        qa_question = user_input

        print('call_llm - chat_history ::', qa_chat_history)
        print('call_llm - question ::', qa_question)

        output = self.qa_module.predict(
            query=qa_question,
            chat_history=qa_chat_history,
        )

        print('call_llm - input ::', user_input)
        print('call_llm - output ::', output)
        qa_answer = output['answer']
        return qa_answer


if __name__ == '__main__':
    bot = OpenAILangchainBot()
    chat_history = []
    query = 'Describe questions for behavioral interviews'
    answer = bot.call_llm({'question': query, 'chat_history': chat_history})
    print(answer)
