from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()




client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY"),
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "find about desi chess factory"}
  ]
)

print(completion.choices[0].message);
