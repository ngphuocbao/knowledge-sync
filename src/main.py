from scraper import fetch_articles, convert_to_markdown, save_markdown


def main():
    articles = fetch_articles()

    print(f"\nTotal articles: {len(articles)}\n")

    for article in articles:
        markdown = convert_to_markdown(article)
        save_markdown(article, markdown)

    print(f"\nSaved {len(articles)} Markdown files.")


if __name__ == "__main__":
    main()