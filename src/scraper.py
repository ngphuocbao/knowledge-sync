"""
scraper.py

This module retrieves knowledge base articles from the OptiSigns
Zendesk Help Center API and converts article HTML into Markdown.

Current functionality:
- Fetch all articles using Zendesk pagination.
- Convert article HTML into clean Markdown.
"""

import requests
from markdownify import markdownify as md

import re
from pathlib import Path

# Zendesk Help Center API endpoint.
# "{}" will be replaced by the current page number.
BASE_URL = "https://support.optisigns.com/api/v2/help_center/en-us/articles.json?page={}"


def fetch_articles():
    """
    Retrieve all articles from the OptiSigns Help Center.

    Returns:
        list: A list containing every article returned by the API.

    Notes:
        - Zendesk returns articles in pages.
        - We continue requesting pages until 'next_page' becomes None.
    """

    all_articles = []
    page = 1

    while True:
        response = requests.get(BASE_URL.format(page))
        response.raise_for_status()

        data = response.json()
        articles = data["articles"]

        all_articles.extend(articles)

        print(f"Fetched page {page}: {len(articles)} articles")

        if data["next_page"] is None:
            break

        page += 1

    return all_articles


def convert_to_markdown(article):
    """
    Convert a Zendesk article from HTML to Markdown.

    Args:
        article (dict): A single article returned by the Zendesk API.

    Returns:
        str: Markdown representation of the article.
    """

    title = article["title"]
    article_url = article["html_url"]
    body = article["body"]

    markdown_body = md(
        body,
        heading_style="ATX",
        bullets="-",
    )

    markdown = (
        f"# {title}\n\n"
        f"**Article URL:** {article_url}\n\n"
        f"---\n\n"
        f"{markdown_body}"
    )

    return markdown

OUTPUT_DIR = Path("knowledge")


def generate_filename(article):
    """
    Generate a safe Markdown filename from article title.

    Args:
        article (dict): A single article returned by the Zendesk API.

    Returns:
        str: A safe Markdown filename.
    """

    title = article["title"].lower()

    # Replace non-alphanumeric characters with hyphens.
    slug = re.sub(r"[^a-z0-9]+", "-", title)

    # Remove leading and trailing hyphens.
    slug = slug.strip("-")

    return f"{slug}.md"


def save_markdown(article, markdown):
    """
    Save Markdown content into the knowledge folder.

    Args:
        article (dict): A single article returned by the Zendesk API.
        markdown (str): Markdown representation of the article.
    """

    OUTPUT_DIR.mkdir(exist_ok=True)

    filename = generate_filename(article)
    file_path = OUTPUT_DIR / filename

    file_path.write_text(markdown, encoding="utf-8")

    print(f"Saved: {file_path}")