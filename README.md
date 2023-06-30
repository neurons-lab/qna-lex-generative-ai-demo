# Lex Bot with Open AI

## Description

This project is a demo of Lex Bot based on Open AI LLM and Kendra index data.

## Prerequisites

* Create parameter in AWS with OpenAI API key and update parameter path in `app.py` in `OPENAI_KEY_PATH` variable.
* Place documents for indexing in directory and change path in `app.py` in `DOCUMENTS_PATH` variable.

## Deployment

```bash
cdk deploy
```

## After Deployment

* In Kendra index data sources press 'Sync now' to start indexing of documents.
* In Lex bot 'Intents' configuration press 'Build'.
* In Lex bot 'Channel integrations' add and configure new channel to Slack.

## Additional information

Youtube guide about Slack App creation and configuration in details:

https://www.youtube.com/watch?v=fak-223hHTE

AWS guide about Slack integration:

https://docs.aws.amazon.com/lexv2/latest/dg/slack-step-4.html
