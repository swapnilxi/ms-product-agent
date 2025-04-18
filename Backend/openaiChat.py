from openai import OpenAI

client = OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "find about desi chess factory"}
  ]
)

print(completion.choices[0].message);
