"""
main.py

Main entry point for the knowledge synchronization job.

The job:
1. Fetches articles from the Zendesk Help Center API.
2. Converts and saves articles as Markdown.
3. Uploads Markdown documents to Gemini File Search.

Delta detection and selective uploads will be added in the next stage.
"""

from scraper import (
    convert_to_markdown,
    fetch_articles,
    save_markdown,
)

from gemini_store import (
    create_client,
    create_file_search_store,
    upload_all_markdown_files,
)


def run_scraper():
    """
    Fetch all Help Center articles and save them as Markdown.

    Returns:
        list: Articles retrieved from the Zendesk API.
    """

    print("\n" + "=" * 50)
    print("SCRAPE -> MARKDOWN")
    print("=" * 50)

    articles = fetch_articles()

    for article in articles:
        markdown = convert_to_markdown(article)
        save_markdown(article, markdown)

    print(f"\nProcessed articles: {len(articles)}")

    return articles


def run_uploader():
    """
    Create a Gemini File Search Store and upload Markdown files.

    Returns:
        object: The created Gemini File Search Store.
    """

    print("\n" + "=" * 50)
    print("MARKDOWN -> GEMINI FILE SEARCH")
    print("=" * 50)

    client = create_client()
    store = create_file_search_store(client)

    upload_all_markdown_files(client, store)

    print(f"\nStore name: {store.name}")

    return store


def main():
    """Run the knowledge synchronization workflow once."""

    print("\nKnowledge synchronization job started.")

    run_scraper()
    run_uploader()

    print("\nKnowledge synchronization job completed successfully.")


if __name__ == "__main__":
    main()