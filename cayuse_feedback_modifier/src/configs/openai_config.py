import os
from openai import OpenAI

# Initialize the client
client = OpenAI(api_key=os.getenv('OPEN_AI_API_KEY'))

# def askGPT(request):
#     completion = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {
#                 "role": "user",
#                 "content": request
#             }
#         ]
#     )
#     return completion.choices[0].message.content