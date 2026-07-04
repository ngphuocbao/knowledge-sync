"""
gemini_store.py

Synchronize local Markdown knowledge files with a Gemini
File Search Store.

The synchronization workflow:
- Calculate a SHA-256 hash for each Markdown file.
- Compare the hash with metadata stored in Gemini.
- Detect added, updated, and unchanged documents.
- Upload only added or updated documents.
"""

import hashlib
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai


KNOWLEDGE_DIR = Path("knowledge")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 10
POLL_INTERVAL_SECONDS = 5

MAX_TOKENS_PER_CHUNK = 500
MAX_OVERLAP_TOKENS = 50


def create_client():
    """
    Create a Gemini API client using the configured API key.
    """
    api_key = os.getenv("API_KEY")

    if not api_key:
        raise ValueError(
        "API key is missing. Set API_KEY."
        )

    return genai.Client(api_key=api_key)


def get_store_name():
    """Read the persistent Gemini File Search Store name."""
    load_dotenv()

    store_name = os.getenv("GEMINI_FILE_SEARCH_STORE")

    if not store_name:
        raise ValueError(
            "GEMINI_FILE_SEARCH_STORE is missing."
        )

    return store_name


def get_markdown_files():
    """
    Return Markdown files that should be synchronized.

    SYNC_LIMIT is optional and is intended for development testing.
    When it is not set, every Markdown file is processed.
    """
    markdown_files = sorted(KNOWLEDGE_DIR.glob("*.md"))

    if not markdown_files:
        raise FileNotFoundError(
            "No Markdown files found in the knowledge directory."
        )

    sync_limit = os.getenv("SYNC_LIMIT")

    if sync_limit:
        limit = int(sync_limit)

        if limit <= 0:
            raise ValueError("SYNC_LIMIT must be greater than zero.")

        markdown_files = markdown_files[:limit]

    return markdown_files


def calculate_file_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    file_content = file_path.read_bytes()

    return hashlib.sha256(file_content).hexdigest()


def get_metadata_value(document, key):
    """Read a string value from Gemini document custom metadata."""
    metadata_items = document.custom_metadata or []

    for metadata in metadata_items:
        if metadata.key == key:
            return metadata.string_value

    return None


def get_existing_documents(client, store_name):
    """
    Load existing documents from the Gemini File Search Store.

    Documents are indexed by display name so they can be compared
    with local Markdown filenames.
    """
    existing_documents = {}

    documents = client.file_search_stores.documents.list(
        parent=store_name
    )

    for document in documents:
        if document.display_name:
            existing_documents[document.display_name] = document

    return existing_documents


def wait_for_operation(client, operation):
    """Wait until a Gemini asynchronous operation has completed."""
    while not operation.done:
        time.sleep(POLL_INTERVAL_SECONDS)
        operation = client.operations.get(operation)

    return operation


def upload_markdown_file(
    client,
    store_name,
    file_path,
    content_hash,
):
    """Upload and index one Markdown document."""
    operation = client.file_search_stores.upload_to_file_search_store(
        file=str(file_path),
        file_search_store_name=store_name,
        config={
            "display_name": file_path.name,
            "mime_type": "text/markdown",
            "custom_metadata": [
                {
                    "key": "source_filename",
                    "string_value": file_path.name,
                },
                {
                    "key": "content_hash",
                    "string_value": content_hash,
                },
            ],
            "chunking_config": {
                "white_space_config": {
                    "max_tokens_per_chunk": MAX_TOKENS_PER_CHUNK,
                    "max_overlap_tokens": MAX_OVERLAP_TOKENS,
                }
            },
        },
    )

    wait_for_operation(client, operation)


def upload_with_retry(
    client,
    store_name,
    file_path,
    content_hash,
):
    """Upload a document with retry handling."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            upload_markdown_file(
                client,
                store_name,
                file_path,
                content_hash,
            )

            return True

        except Exception as error:
            print(
                f"    Upload failed "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )
            print(f"    {error}")

            if attempt < MAX_RETRIES:
                print(
                    f"    Retrying in "
                    f"{RETRY_DELAY_SECONDS} seconds..."
                )

                time.sleep(RETRY_DELAY_SECONDS)

    return False


def sync_markdown_files(client, store_name):
    """
    Synchronize local Markdown files with Gemini File Search.

    Returns:
        dict: Counts for added, updated, skipped, and failed documents.
    """
    markdown_files = get_markdown_files()

    print("\nLoading existing Gemini documents...")

    existing_documents = get_existing_documents(
        client,
        store_name,
    )

    print(
        f"Existing documents: {len(existing_documents)}"
    )

    counts = {
        "added": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    }

    total_files = len(markdown_files)

    print(f"Markdown files to check: {total_files}\n")

    for index, file_path in enumerate(
        markdown_files,
        start=1,
    ):
        content_hash = calculate_file_hash(file_path)

        existing_document = existing_documents.get(
            file_path.name
        )

        if existing_document is None:
            action = "added"

        else:
            stored_hash = get_metadata_value(
                existing_document,
                "content_hash",
            )

            if stored_hash == content_hash:
                counts["skipped"] += 1

                print(
                    f"[{index}/{total_files}] "
                    f"SKIPPED: {file_path.name}"
                )

                continue

            action = "updated"

        print(
            f"[{index}/{total_files}] "
            f"{action.upper()}: {file_path.name}"
        )

        upload_success = upload_with_retry(
            client,
            store_name,
            file_path,
            content_hash,
        )

        if not upload_success:
            counts["failed"] += 1

            print(f"    FAILED: {file_path.name}\n")

            continue

        if action == "updated":
            client.file_search_stores.documents.delete(
                name=existing_document.name,
                config={
                    "force": True,
                },
            )

        counts[action] += 1

        print("    Success\n")

    print("=" * 50)
    print("SYNC SUMMARY")
    print("=" * 50)
    print(f"Added   : {counts['added']}")
    print(f"Updated : {counts['updated']}")
    print(f"Skipped : {counts['skipped']}")
    print(f"Failed  : {counts['failed']}")
    print(
        "Chunk strategy : "
        f"{MAX_TOKENS_PER_CHUNK} tokens / "
        f"{MAX_OVERLAP_TOKENS} overlap"
    )
    print("=" * 50)

    return counts


def main():
    """Run the Gemini document synchronization workflow."""
    client = create_client()
    store_name = get_store_name()

    print(f"\nStore name: {store_name}")

    sync_markdown_files(
        client,
        store_name,
    )


if __name__ == "__main__":
    main()