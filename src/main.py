"""
main.py

Main entry point for the daily knowledge synchronization job.

Workflow:
1. Fetch OptiSigns Help Center articles.
2. Convert and save articles as Markdown.
3. Detect added or updated documents.
4. Upload only the delta to Gemini File Search.
5. Print synchronization counts and exit.
"""

from scraper import (
    convert_to_markdown,
    fetch_articles,
    save_markdown,
)

from gemini_store import (
    create_client,
    get_store_name,
    sync_markdown_files,
)


def run_scraper():
    """
    Fetch all Help Center articles and save them as Markdown.

    Returns:
        int: Number of processed articles.
    """
    print("\n" + "=" * 50)
    print("SCRAPE -> MARKDOWN")
    print("=" * 50)

    articles = fetch_articles()

    for article in articles:
        markdown = convert_to_markdown(article)
        save_markdown(article, markdown)

    processed_count = len(articles)

    print(f"\nProcessed articles: {processed_count}")

    return processed_count


def run_sync():
    """
    Synchronize Markdown documents with Gemini File Search.

    Returns:
        dict: Synchronization counts.
    """
    print("\n" + "=" * 50)
    print("MARKDOWN -> GEMINI FILE SEARCH")
    print("=" * 50)

    client = create_client()
    store_name = get_store_name()

    print(f"\nStore name: {store_name}")

    return sync_markdown_files(
        client,
        store_name,
    )


def main():
    """Run the knowledge synchronization job once."""
    print("\nKnowledge synchronization job started.")

    processed_count = run_scraper()
    counts = run_sync()

    if counts["failed"] > 0:
        raise RuntimeError(
            f"Knowledge synchronization failed for "
            f"{counts['failed']} document(s)."
        )

    print("\n" + "=" * 50)
    print("JOB SUMMARY")
    print("=" * 50)
    print(f"Processed: {processed_count}")
    print(f"Added    : {counts['added']}")
    print(f"Updated  : {counts['updated']}")
    print(f"Skipped  : {counts['skipped']}")
    print(f"Failed   : {counts['failed']}")
    print("=" * 50)

    print(
        "\nKnowledge synchronization job "
        "completed successfully."
    )


if __name__ == "__main__":
    main()