from groq import Groq

client = Groq()

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "user",
            "content": "Explain photosynthesis in one sentence."
        }
    ]
)

print(response.choices[0].message.content)