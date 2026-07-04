"""
gemini_store.py

Create a Gemini File Search Store and upload Markdown files
from the local knowledge/ folder.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai


KNOWLEDGE_DIR = Path("knowledge")
STORE_DISPLAY_NAME = "knowledge-sync-opti-bot"

MAX_UPLOAD_FILES = 50
MAX_RETRIES = 3


def create_client():
    """
    Create a Gemini API client from an environment variable.

    API_KEY is used for container and cloud deployment.
    GEMINI_API_KEY is kept as a local development fallback.
    """
    load_dotenv()

    api_key = os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "API key is missing. Set API_KEY or GEMINI_API_KEY."
        )

    return genai.Client(api_key=api_key)


def create_file_search_store(client):
    """Create a new Gemini File Search Store."""
    store = client.file_search_stores.create(
        config={
            "display_name": STORE_DISPLAY_NAME,
            "embedding_model": "models/gemini-embedding-2",
        }
    )

    print(f"Created store: {store.name}")
    return store


def select_markdown_files():
    """Select representative Markdown files for vector store upload."""

    all_files = sorted(KNOWLEDGE_DIR.glob("*.md"))

    priority_keywords = [
        "youtube",
        "playlist",
        "screen",
        "asset",
        "schedule",
        "google",
        "powerpoint",
        "pdf",
        "canva",
        "dashboard",
        "weather",
        "device",
    ]

    selected = []

    for keyword in priority_keywords:
        for file_path in all_files:
            if keyword in file_path.name and file_path not in selected:
                selected.append(file_path)

    for file_path in all_files:
        if file_path not in selected:
            selected.append(file_path)

    return selected[:MAX_UPLOAD_FILES]


def upload_all_markdown_files(client, store):
    """Upload Markdown files to the Gemini File Search Store."""

    markdown_files = select_markdown_files()

    if not markdown_files:
        raise FileNotFoundError("No Markdown files found.")

    print(f"\nFound {len(markdown_files)} Markdown files.\n")

    uploaded_count = 0

    for file_path in markdown_files:

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                print(f"Uploading ({uploaded_count + 1}/{len(markdown_files)}): {file_path.name}")

                operation = client.file_search_stores.upload_to_file_search_store(
                    file=str(file_path),
                    file_search_store_name=store.name,
                    config={
                        "display_name": file_path.name,
                        "chunking_config": {
                            "white_space_config": {
                                "max_tokens_per_chunk": 500,
                                "max_overlap_tokens": 50,
                            }
                        },
                    },
                )

                while not operation.done:
                    print("    Waiting for indexing...")
                    time.sleep(5)
                    operation = client.operations.get(operation)

                uploaded_count += 1

                print("Success\n")

                break

            except Exception as e:

                print(f"    Upload failed (attempt {attempt}/{MAX_RETRIES})")
                print(f"    {e}")

                if attempt < MAX_RETRIES:
                    print("    Retrying in 10 seconds...\n")
                    time.sleep(10)
                else:
                    print(f"    Skipped: {file_path.name}\n")

    print("=" * 50)
    print(f"Uploaded files : {uploaded_count}")
    print(f"Requested      : {len(markdown_files)}")
    print("Chunk strategy : 500 tokens / 50 overlap")
    print("=" * 50)


def main():
    """Create a File Search Store and upload all Markdown files."""
    client = create_client()
    store = create_file_search_store(client)

    upload_all_markdown_files(client, store)
    print(f"\nStore name: {store.name}")

if __name__ == "__main__":
    main()