"""Krok 1 – crawler: zber odkazov zo stránky do zadanej hĺbky.

Výstup: CSV so surovými hranami `source,target` (vrátane duplicít).

Použitie:
    python crawler.py                                  # lua.org, hĺbka 2
    python crawler.py --url https://example.com/ --depth 3 --out data/raw_edges.csv
"""
import argparse
import csv
import time
from collections import deque
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

DEFAULT_URL = "https://www.lua.org/"
DEFAULT_DEPTH = 2
DEFAULT_OUT = Path("data/raw_edges.csv")

DELAY = 0.3    # pauza medzi requestmi (s), aby sme server nezaťažovali
TIMEOUT = 10   # timeout jedného requestu (s)
HEADERS = {"User-Agent": "Mozilla/5.0 (PageRank school project)"}

# domény sociálnych sietí – odkazy na ne sa zahadzujú
SOCIAL_DOMAINS = {
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com",
    "tiktok.com", "pinterest.com", "discord.gg", "discord.com", "discordapp.com",
}

# prípony súborov, ktoré nie sú HTML stránky
SKIP_EXTENSIONS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".webp",
    ".zip", ".gz", ".tgz", ".tar", ".bz2", ".xz", ".rar", ".7z", ".exe", ".dmg",
    ".css", ".js", ".rss", ".xml", ".txt", ".ps", ".mp3", ".mp4", ".avi",
)


def bare_host(netloc: str) -> str:
    """'www.lua.org:443' -> 'lua.org' (na porovnávanie domén)."""
    netloc = netloc.lower().split(":")[0]
    return netloc[4:] if netloc.startswith("www.") else netloc


class Crawler:
    def __init__(self, start_url: str, max_depth: int):
        self.start_host = urlparse(start_url).netloc.lower()
        self.start_url = self.normalize_url(start_url, start_url)
        self.max_depth = max_depth
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.stats = {"footer": 0, "social": 0, "not_page": 0}

    # ---------- URL pomocné funkcie ----------

    def is_internal(self, url: str) -> bool:
        return bare_host(urlparse(url).netloc) == bare_host(self.start_host)

    @staticmethod
    def is_social(url: str) -> bool:
        host = bare_host(urlparse(url).netloc)
        return any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS)

    def normalize_url(self, href: str, base_url: str) -> str | None:
        """Prevedie href na absolútnu, normalizovanú URL. Vráti None, ak odkaz nie je stránka."""
        href = href.strip()
        if not href:
            return None
        url, _fragment = urldefrag(urljoin(base_url, href))   # relatívne -> absolútne, bez #...
        parts = urlparse(url)
        if parts.scheme not in ("http", "https"):          # mailto:, javascript:, ftp:, ...
            return None
        if parts.path.lower().endswith(SKIP_EXTENSIONS):   # obrázky, archívy, pdf, ...
            return None

        scheme, netloc, path = parts.scheme, parts.netloc.lower(), parts.path or "/"
        if self.is_internal(url):
            # interné stránky zjednotíme na tvar https://<štartovací host>/...
            scheme, netloc = "https", self.start_host
        if path.endswith(("/index.html", "/index.htm")):
            path = path[: path.rfind("/") + 1]
        return urlunparse((scheme, netloc, path, "", parts.query, ""))

    # ---------- sťahovanie a parsovanie ----------

    def fetch_html(self, url: str) -> str | None:
        """Stiahne stránku; vráti HTML alebo None (chyba / nie je to HTML)."""
        try:
            r = self.session.get(url, timeout=TIMEOUT)
        except requests.RequestException as e:
            print(f"  ! chyba: {url} ({type(e).__name__})")
            return None
        if r.status_code != 200:
            print(f"  ! HTTP {r.status_code}: {url}")
            return None
        if "text/html" not in r.headers.get("Content-Type", ""):
            return None
        return r.text

    def extract_links(self, html: str, page_url: str) -> list[str]:
        """Vráti zoznam (aj s duplicitami) normalizovaných odkazov zo stránky, bez footeru."""
        soup = BeautifulSoup(html, "html.parser")

        # 1) odstránenie footeru: <footer> a prvky s 'footer' v class/id
        footers = soup.find_all("footer")
        footers += soup.find_all(class_=lambda c: c and "footer" in c.lower())
        footers += soup.find_all(id=lambda i: i and "footer" in i.lower())
        for el in footers:
            if el.decomposed:  # už odstránený ako súčasť iného footeru
                continue
            self.stats["footer"] += len(el.find_all("a", href=True))
            el.decompose()

        # 2) zber odkazov
        links = []
        for a in soup.find_all("a", href=True):
            url = self.normalize_url(a["href"], page_url)
            if url is None:
                self.stats["not_page"] += 1
            elif self.is_social(url):
                self.stats["social"] += 1
            else:
                links.append(url)
        return links

    # ---------- samotný crawl ----------

    def crawl(self) -> list[tuple[str, str]]:
        """BFS: stránky v hĺbke < max_depth sa stiahnu a ich odkazy sa uložia ako hrany.

        Ďalej sa sledujú iba interné odkazy; externé zostanú len ako cieľové uzly.
        """
        edges = []
        visited = {self.start_url}
        queue = deque([(self.start_url, 0)])

        while queue:
            url, depth = queue.popleft()
            html = self.fetch_html(url)
            time.sleep(DELAY)
            if html is None:
                continue

            links = self.extract_links(html, url)
            edges.extend((url, target) for target in links)
            print(f"[hĺbka {depth}] {url}  ->  {len(links)} odkazov")

            if depth + 1 < self.max_depth:
                for target in links:
                    if self.is_internal(target) and target not in visited:
                        visited.add(target)
                        queue.append((target, depth + 1))
        return edges


def save_edges(edges: list[tuple[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target"])
        writer.writerows(edges)


def main() -> None:
    parser = argparse.ArgumentParser(description="Zber odkazov zo stránky (crawler).")
    parser.add_argument("--url", default=DEFAULT_URL, help="štartovacia stránka")
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH, help="počet úrovní zanorenia")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="výstupný CSV súbor")
    args = parser.parse_args()

    crawler = Crawler(args.url, args.depth)
    edges = crawler.crawl()
    save_edges(edges, args.out)

    print()
    print(f"Stiahnutých stránok:              {len({s for s, _ in edges})}")
    print(f"Surových hrán (vrátane duplicít): {len(edges)}")
    print(f"Odfiltrované – odkazy vo footeri: {crawler.stats['footer']}")
    print(f"Odfiltrované – sociálne siete:    {crawler.stats['social']}")
    print(f"Odfiltrované – nie sú stránky:    {crawler.stats['not_page']}")
    print(f"Uložené do {args.out}")


if __name__ == "__main__":
    main()
