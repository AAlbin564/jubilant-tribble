import httpx

from app.constants import (
    EXCLUDED_ARTICLE_SECTIONS, HTTP_TIMEOUT_SECONDS, KNOWLEDGE_DIR, MUSHROOM_ARTICLE_TITLES,
    WIKI_SECTION_HEADER, WIKIPEDIA_API_URL, WIKIPEDIA_HEADERS,
)

def is_excluded(header: str) -> bool:
    return any(keyword in header.lower() for keyword in EXCLUDED_ARTICLE_SECTIONS)

def fetch_wiki_article(title: str) -> tuple[str,str] | None:
    params = {
        "action": "query", "prop": "extracts", "explaintext": 1,
        "redirects": 1, "format": "json", "titles": title,
    }

    response = httpx.get(WIKIPEDIA_API_URL, params=params, headers=WIKIPEDIA_HEADERS, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    pages = response.json()["query"]["pages"]
    article = list(pages.values())[0]

    if "extract" not in article:
        return None
    return article["title"], article["extract"]

def trim_article(text: str) -> str:
    """Remove sections not relevant for mushroom foraging."""
    matches = list(WIKI_SECTION_HEADER.finditer(text))
    if not matches:
        return text.strip()

    kept = [text[:matches[0].start()].strip()]  
    skip_level = None  

    for i, match in enumerate(matches):
        level = len(match.group(1))
        name = match.group(2)
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end():body_end].strip()

        if skip_level is not None and level > skip_level:
            continue  
        skip_level = None

        if is_excluded(name):
            skip_level = level
            continue

        kept.append(f"{'#' * level} {name}\n{body}".strip())

    return "\n\n".join(part for part in kept if part)


def main():
    """For each article in MUSHROOM_ARTICLE_TITLES fetch that article then if it exists create a new .md file containing the article contents
    and named after the article attach also header information saying which URL it came from and the license"""

    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    for article_title in MUSHROOM_ARTICLE_TITLES:

        try:
            result = fetch_wiki_article(article_title)
        except httpx.HTTPError as e:
            print(f"Failed to fetch {article_title}: {e}")
            continue

        if result is None:
            print(f"Couldnt find an article with the title {article_title}")
            continue

        title, species_information = result

        species_information = trim_article(species_information)

        filename = title.lower().replace(" ", "_") + ".md"

        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        header = f"# {title}\n\nSource: {url}\nLicense: CC BY-SA 4.0 (Wikipedia)\n\n"

        (KNOWLEDGE_DIR / filename).write_text(header + species_information, encoding="utf-8")

        print(f"finished article: {title}")




if __name__ == "__main__":
    main()




