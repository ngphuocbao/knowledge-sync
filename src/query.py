from google.genai import types

from gemini_store import create_client, get_store_name


SYSTEM_PROMPT = """
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
"""


def main():
    client = create_client()
    store_name = get_store_name()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="How do I add a YouTube video?",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[store_name]
                    )
                )
            ],
        ),
    )

    print(response.text)


if __name__ == "__main__":
    main()