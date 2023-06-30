import aws_cdk as core
import aws_cdk.assertions as assertions

from lexv2_openai_longchain_dispatcher.lexv2_openai_longchain_dispatcher_stack import Lexv2OpenaiLongchainDispatcherStack

# example tests. To run these tests, uncomment this file along with the example
# resource in lexv2_openai_longchain_dispatcher/lexv2_openai_longchain_dispatcher_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Lexv2OpenaiLongchainDispatcherStack(app, "lexv2-openai-longchain-dispatcher")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
