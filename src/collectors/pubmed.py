"""
PubMed research article collector for Trend Engine V2.0.

Retrieves recent research articles from PubMed using the NCBI Entrez
API via the biopython library.
"""

from __future__ import annotations

from typing import Any

from Bio import Entrez


# Default query targeting pain and exercise/rehabilitation research
_DEFAULT_QUERY = (
    '("chronic pain"[Title/Abstract] OR "cancer pain"[Title/Abstract] '
    'OR "sciatica"[Title/Abstract] OR "low back pain"[Title/Abstract] '
    'OR "neck pain"[Title/Abstract]) '
    'AND ("exercise"[Title/Abstract] OR "rehabilitation"[Title/Abstract] '
    'OR "physical therapy"[Title/Abstract] OR "ergonomics"[Title/Abstract])'
)


def collect_pubmed(
    sender_email: str = "",
    query: str = _DEFAULT_QUERY,
    retmax: int = 5,
) -> list[dict[str, Any]] | None:
    """Collect recent PubMed articles matching the pain/exercise query.

    Uses NCBI Entrez to search PubMed for recently published articles
    about chronic pain conditions and exercise/rehabilitation treatments.

    Args:
        sender_email: Email address for NCBI Entrez identification.
            Required by NCBI guidelines. Defaults to empty string.
        query: PubMed search query. Defaults to the pain/exercise query.
        retmax: Maximum number of articles to retrieve.

    Returns:
        A list of article dicts::

            [
                {
                    "title": str,
                    "journal": str,
                    "date": str,
                    "pmid": str
                },
                ...
            ]

        Returns None if the collection fails.
    """
    if sender_email:
        Entrez.email = sender_email
    else:
        Entrez.email = "formcoach-trend-engine@example.com"

    print(f"[PubMed] Searching with retmax={retmax}...")

    # Step 1: Search for matching article IDs
    try:
        search_handle = Entrez.esearch(
            db="pubmed",
            term=query,
            sort="date",
            retmax=retmax,
        )
        search_results = Entrez.read(search_handle)
        search_handle.close()
    except Exception as exc:
        print(f"[PubMed] Search failed: {exc}")
        return None

    id_list = search_results.get("IdList", [])
    if not id_list:
        print("[PubMed] No articles found matching query.")
        return None

    print(f"[PubMed] Found {len(id_list)} article IDs. Fetching details...")

    # Step 2: Fetch article details
    try:
        fetch_handle = Entrez.efetch(
            db="pubmed",
            id=id_list,
            rettype="xml",
            retmode="xml",
        )
        records = Entrez.read(fetch_handle)
        fetch_handle.close()
    except Exception as exc:
        print(f"[PubMed] Fetch failed: {exc}")
        return None

    articles: list[dict[str, Any]] = []

    pubmed_articles = records.get("PubmedArticle", [])
    for record in pubmed_articles:
        try:
            medline = record.get("MedlineCitation", {})
            article_data = medline.get("Article", {})

            # Title
            title = str(article_data.get("ArticleTitle", "No title"))

            # Journal
            journal_info = article_data.get("Journal", {})
            journal = str(journal_info.get("Title", "Unknown journal"))

            # Date — try ArticleDate first, then PubDate
            date_str = ""
            article_dates = article_data.get("ArticleDate", [])
            if article_dates:
                date_obj = article_dates[0]
                year = str(date_obj.get("Year", ""))
                month = str(date_obj.get("Month", "")).zfill(2)
                day = str(date_obj.get("Day", "")).zfill(2)
                date_str = f"{year}-{month}-{day}"
            else:
                pub_date = journal_info.get("JournalIssue", {}).get("PubDate", {})
                year = str(pub_date.get("Year", ""))
                month = str(pub_date.get("Month", ""))
                day = str(pub_date.get("Day", ""))
                parts = [p for p in [year, month, day] if p]
                date_str = "-".join(parts) if parts else "Unknown"

            # PMID
            pmid = str(medline.get("PMID", ""))

            articles.append({
                "title": title,
                "journal": journal,
                "date": date_str,
                "pmid": pmid,
            })

        except Exception as exc:
            print(f"[PubMed] Error parsing article record: {exc}")
            continue

    if not articles:
        print("[PubMed] Failed to parse any articles.")
        return None

    print(f"[PubMed] Collected {len(articles)} articles.")
    return articles
