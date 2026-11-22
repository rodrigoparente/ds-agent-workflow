#!/usr/bin/env python3
"""Search papers on Semantic Scholar (default) or arXiv. Standard library only.

Usage:
    python3 .agents/skills/research/scripts/papers.py search "query" [--source s2|arxiv]
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

S2 = "https://api.semanticscholar.org/graph/v1/paper/search"
ARXIV = "https://export.arxiv.org/api/query"
ATOM = "{http://www.w3.org/2005/Atom}"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "research-skill"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def _xml_text(elem: ET.Element, tag: str) -> str:
    node = elem.find(tag)
    return (node.text or "").strip() if node is not None and node.text else ""


def show(title, year, authors, extra, url, abstract):
    print(f"- {title} ({year})")
    print(f"  {', '.join(authors[:4])}{' et al.' if len(authors) > 4 else ''}")
    print(f"  {extra} | {url}")
    if abstract:
        print(f"  {abstract[:300].strip()}...")
    print()


def search_s2(query: str, limit: int) -> None:
    fields = "title,year,authors,citationCount,externalIds,abstract,url"
    params = urllib.parse.urlencode({"query": query, "limit": limit, "fields": fields})
    data = json.loads(get(f"{S2}?{params}")).get("data", [])
    for p in data:
        arxiv_id = (p.get("externalIds") or {}).get("ArXiv")
        extra = f"{p.get('citationCount', 0)} citations"
        if arxiv_id:
            extra += f" | arXiv:{arxiv_id}"
        authors = [a["name"] for a in p.get("authors", []) if a.get("name")]
        show(p.get("title", ""), p.get("year"), authors, extra, p.get("url", ""), p.get("abstract"))


def search_arxiv(query: str, limit: int) -> None:
    terms = " AND ".join(f"all:{w}" for w in query.split())
    params = urllib.parse.urlencode(
        {"search_query": terms, "max_results": limit, "sortBy": "relevance"}
    )
    root = ET.fromstring(get(f"{ARXIV}?{params}"))
    for e in root.findall(f"{ATOM}entry"):
        url = _xml_text(e, f"{ATOM}id")
        authors = [
            name for a in e.findall(f"{ATOM}author") if (name := _xml_text(a, f"{ATOM}name"))
        ]
        title = " ".join(_xml_text(e, f"{ATOM}title").split())
        abstract = " ".join(_xml_text(e, f"{ATOM}summary").split())
        year = _xml_text(e, f"{ATOM}published")[:4]
        arxiv_id = url.split("/abs/")[-1] if "/abs/" in url else url
        show(title, year, authors, f"arXiv:{arxiv_id}", url, abstract)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--source", choices=["s2", "arxiv"], default="s2")
    s.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    try:
        (search_s2 if args.source == "s2" else search_arxiv)(args.query, args.limit)
    except urllib.error.HTTPError as e:
        print(
            f"Request failed: HTTP {e.code}. Semantic Scholar may be rate-limiting; "
            "retry shortly or use --source arxiv.",
            file=sys.stderr,
        )
        sys.exit(1)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"Network error while querying papers: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
