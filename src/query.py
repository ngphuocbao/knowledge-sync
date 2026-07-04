import os
from dotenv import load_dotenv
from google import genai
from google.genai import types


STORE_NAME = "fileSearchStores/knowledgesyncoptibot-kv5mwqorazi4"


SYSTEM_PROMPT = """
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
"""


def main():
    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="How do I add a YouTube video?",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[STORE_NAME]
                    )
                )
            ],
        ),
    )

    print(response.text)


if __name__ == "__main__":
    main()