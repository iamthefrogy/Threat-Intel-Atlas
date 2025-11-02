#!/usr/bin/env python3
"""
Threat Intel Atlas content pipeline.

Fetches RSS feeds, deduplicates entries, enriches them with light metadata,
persists cache/history, and renders README plus static site assets.
"""
from __future__ import annotations

import asyncio
import json
import textwrap
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import aiohttp
import feedparser
import yaml
from dateutil import parser as date_parser
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SITE_DATA_DIR = ROOT / "site" / "data"
CACHE_PATH = DATA_DIR / "cache.json"
FULL_PATH = DATA_DIR / "full.json"
LATEST_PATH = DATA_DIR / "latest.json"
LATEST_MARKDOWN_PATH = DATA_DIR / "latest.md"
SITE_DATA_PATH = SITE_DATA_DIR / "latest.json"
README_TEMPLATE = ROOT / "README.template.md"
README_OUTPUT = ROOT / "README.md"
SITE_TEMPLATE = ROOT / "site" / "index.template.html"
SITE_OUTPUT = ROOT / "site" / "index.html"
FEEDS_PATH = ROOT / "feeds.yaml"

# Limit history to keep repo size manageable
MAX_HISTORY_ITEMS = 1000
MAX_LATEST_ITEMS = 200
README_ITEMS = 40
README_DAYS = 7

# Keyword buckets for light-touch tagging
KEYWORD_TAGS: Dict[str, Tuple[str, ...]] = {
    "malware": (
        "ransomware",
        "malware",
        "botnet",
        "trojan",
        "infostealer",
        "rootkit",
        "loader",
    ),
    "vulnerabilities": (
        "cve-",
        "vulnerability",
        "zero-day",
        "privilege escalation",
        "remote code execution",
    ),
    "apt": ("apt", "advanced persistent threat", "nation-state", "state-sponsored"),
    "phishing": ("phishing", "social engineering"),
    "cloud": ("cloud", "azure", "aws", "gcp", "kubernetes"),
    "iot": ("iot", "industrial control", "scada", "ot security"),
    "defense": ("mitigation", "detection", "defender", "hardening"),
}


@dataclass(frozen=True)
class Feed:
    name: str
    url: str
    category: Optional[str] = None


@dataclass
class Entry:
    uid: str
    title: str
    link: str
    summary: str
    published: datetime
    source: str
    category: Optional[str]
    tags: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uid": self.uid,
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "published": self.published.replace(tzinfo=timezone.utc).isoformat(),
            "source": self.source,
            "category": self.category,
            "tags": list(self.tags),
        }


def load_feeds(path: Path) -> List[Feed]:
    if not path.exists():
        raise FileNotFoundError(f"Feed definition file is missing: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    feeds_data = raw.get("feeds") if isinstance(raw, dict) else None
    if not feeds_data:
        raise ValueError("feeds.yaml does not contain any feeds under 'feeds'.")
    feeds: List[Feed] = []
    for item in feeds_data:
        name = item.get("name")
        url = item.get("url")
        if not name or not url:
            continue
        feeds.append(Feed(name=name.strip(), url=url.strip(), category=item.get("category")))
    return feeds


def normalise_summary(summary: str, limit: int = 420) -> str:
    if not summary:
        return ""
    cleaned = " ".join(summary.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def parse_datetime(entry: feedparser.FeedParserDict) -> datetime:
    candidates: Iterable[Optional[str]] = (
        entry.get("published"),
        entry.get("updated"),
        entry.get("created"),
    )
    structured_candidates: Iterable[Any] = (
        entry.get("published_parsed"),
        entry.get("updated_parsed"),
        entry.get("created_parsed"),
    )
    for struct in structured_candidates:
        if struct:
            return datetime(*struct[:6], tzinfo=timezone.utc)
    for candidate in candidates:
        if candidate:
            try:
                dt = date_parser.parse(candidate)
                if not dt.tzinfo:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (ValueError, TypeError, OverflowError):
                continue
    # Fallback to now if nothing usable is present
    return datetime.now(tz=timezone.utc)


def fingerprint(entry: feedparser.FeedParserDict) -> str:
    for key in ("id", "guid", "link"):
        value = entry.get(key)
        if value:
            return value.strip()
    title = entry.get("title", "")
    link = entry.get("link", "")
    return f"{title}-{link}".strip() or str(hash(title))


def compute_tags(entry: feedparser.FeedParserDict, extra: Optional[str] = "") -> Tuple[str, ...]:
    corpus = " ".join(
        segment.lower()
        for segment in (
            entry.get("title", ""),
            entry.get("summary", ""),
            entry.get("description", ""),
            extra or "",
        )
        if segment
    )
    tags: set[str] = set()
    for tag, keywords in KEYWORD_TAGS.items():
        if any(keyword in corpus for keyword in keywords):
            tags.add(tag)
    return tuple(sorted(tags))


async def fetch_feed_entries(session: aiohttp.ClientSession, feed: Feed) -> Tuple[Feed, List[Entry], Optional[str]]:
    try:
        async with session.get(feed.url, timeout=aiohttp.ClientTimeout(total=25)) as response:
            response.raise_for_status()
            payload = await response.text()
    except Exception as exc:  # noqa: BLE001
        return feed, [], f"{exc}"

    parsed = feedparser.parse(payload)
    entries: List[Entry] = []
    for entry in parsed.entries:
        uid = fingerprint(entry)
        link = entry.get("link") or ""
        title = entry.get("title") or "Untitled"
        summary = entry.get("summary") or entry.get("description") or ""
        published = parse_datetime(entry)
        tags = compute_tags(entry, extra=feed.category)
        entries.append(
            Entry(
                uid=uid,
                title=title.strip(),
                link=link.strip(),
                summary=normalise_summary(summary),
                published=published,
                source=feed.name,
                category=feed.category,
                tags=tags,
            )
        )
    return feed, entries, None


async def gather_entries(feeds: List[Feed]) -> Tuple[List[Entry], Dict[str, str]]:
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {"User-Agent": "Threat-Intel-Atlas/1.0 (+https://github.com/)"}
    connector = aiohttp.TCPConnector(limit=12, ttl_dns_cache=300)
    errors: Dict[str, str] = {}
    collected: List[Entry] = []

    async with aiohttp.ClientSession(timeout=timeout, headers=headers, connector=connector) as session:
        tasks = [fetch_feed_entries(session, feed) for feed in feeds]
        for result in await asyncio.gather(*tasks):
            feed, entries, err = result
            if err:
                errors[feed.name] = err
                continue
            collected.extend(entries)

    return collected, errors


def load_existing_cache(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"items": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"items": []}


def merge_items(existing: Iterable[Dict[str, Any]], new_entries: List[Entry]) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for item in existing:
        uid = item.get("uid")
        if uid:
            merged[uid] = item
    for entry in new_entries:
        merged[entry.uid] = entry.to_dict()
    items = list(merged.values())
    items.sort(key=lambda item: item.get("published", ""), reverse=True)
    return items[:MAX_HISTORY_ITEMS]


def summarise(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now.timestamp() - 24 * 3600
    recent = [
        entry
        for entry in entries
        if datetime.fromisoformat(entry["published"]).timestamp() >= cutoff
    ]

    per_source: Dict[str, int] = defaultdict(int)
    per_tag: Dict[str, int] = defaultdict(int)
    for entry in recent:
        per_source[entry["source"]] += 1
        for tag in entry.get("tags", []):
            per_tag[tag] += 1

    return {
        "recent_count": len(recent),
        "total_count": len(entries),
        "top_sources": sorted(per_source.items(), key=lambda item: item[1], reverse=True)[:5],
        "top_tags": sorted(per_tag.items(), key=lambda item: item[1], reverse=True)[:5],
    }


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def render_templates(context: Dict[str, Any]) -> None:
    env = Environment(
        loader=FileSystemLoader(str(ROOT)),
        autoescape=select_autoescape(
            enabled_extensions=("html",),
            default_for_string=False,
            default=False,
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    readme_template = env.get_template("README.template.md")
    site_template = env.get_template("site/index.template.html")

    README_OUTPUT.write_text(readme_template.render(**context), encoding="utf-8")
    SITE_OUTPUT.write_text(site_template.render(**context), encoding="utf-8")


def filter_recent_entries(items: List[Dict[str, Any]], *, days: int) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent: List[Dict[str, Any]] = []
    for item in items:
        published = item.get("published")
        if not published:
            continue
        try:
            published_dt = datetime.fromisoformat(published)
        except ValueError:
            continue
        if published_dt.tzinfo is None:
            published_dt = published_dt.replace(tzinfo=timezone.utc)
        if published_dt >= cutoff:
            recent.append(item)
    recent.sort(key=lambda record: record.get("published", ""), reverse=True)
    return recent


def escape_table_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ").strip()


def build_markdown_table(
    items: List[Dict[str, Any]],
    *,
    limit: int = README_ITEMS,
    placeholder: str = "> _No signals detected in the last 7 days._",
) -> str:
    visible = items[:limit]
    if not visible:
        return placeholder

    header = "| Title | Tags | Published (UTC) |\n| --- | --- | --- |"
    rows: List[str] = [header]
    for item in visible:
        title = escape_table_cell(item.get("title", "Untitled"))
        link = item.get("link", "").strip()
        title_cell = f"[{title}]({link})" if link else title
        tags = ", ".join(item.get("tags", [])) or "unclassified"
        tags_cell = escape_table_cell(tags)
        published_raw = item.get("published", "")
        try:
            published_cell = datetime.fromisoformat(published_raw).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            published_cell = published_raw
        rows.append(f"| {title_cell} | {tags_cell} | {escape_table_cell(published_cell)} |")
    return "\n".join(rows)


def main() -> None:
    ensure_directories()
    feeds = load_feeds(FEEDS_PATH)
    fetched_entries, errors = asyncio.run(gather_entries(feeds))

    cache = load_existing_cache(CACHE_PATH)
    merged_items = merge_items(cache.get("items", []), fetched_entries)

    latest_items = merged_items[:MAX_LATEST_ITEMS]
    weekly_items = filter_recent_entries(merged_items, days=README_DAYS)
    generated_at = datetime.now(tz=timezone.utc)

    summary = summarise(merged_items)
    markdown_snippet = build_markdown_table(
        weekly_items,
        placeholder="No signals detected in the last 7 days.",
    )

    context = {
        "generated_at": generated_at,
        "generated_at_iso": generated_at.isoformat(),
        "feeds_count": len(feeds),
        "latest_items": latest_items,
        "weekly_items": weekly_items,
        "weekly_count": len(weekly_items),
        "summary": summary,
        "errors": errors,
        "markdown_snippet": markdown_snippet,
    }

    CACHE_PATH.write_text(json.dumps({"items": merged_items, "generated_at": generated_at.isoformat()}, indent=2), encoding="utf-8")
    FULL_PATH.write_text(json.dumps(merged_items, indent=2), encoding="utf-8")
    LATEST_PATH.write_text(json.dumps(latest_items, indent=2), encoding="utf-8")
    SITE_DATA_PATH.write_text(json.dumps(context, indent=2, default=str), encoding="utf-8")
    LATEST_MARKDOWN_PATH.write_text(markdown_snippet, encoding="utf-8")

    render_templates(context)


if __name__ == "__main__":
    main()
