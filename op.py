import openai
openai.api_key = "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"

models = openai.Model.list()
for m in models['data']:
    print(m['id'])
