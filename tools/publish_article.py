#!/usr/bin/env python3
"""Terbitkan artikel blog KONIG dari file JSON.

Pemakaian:  python3 tools/publish_article.py artikel.json

Format JSON:
{
  "slug": "coating-mobil-gading-serpong-musim-hujan",   # huruf kecil, angka, tanda hubung
  "title": "Judul H1 lengkap artikel",
  "seoTitle": "Title tag (<= 60 karakter) | KONÏG",       # opsional, default = title
  "metaDescription": "<= 155 karakter",
  "excerpt": "1-2 kalimat untuk kartu di halaman /blog",
  "date": "2026-11-13",                                   # YYYY-MM-DD
  "intro": "paragraf pembuka (mini-markdown)",
  "sections": [{"heading": "Sub judul", "body": "mini-markdown"}],
  "cta": {"heading": "...", "body": "..."},               # opsional, default CTA KONIG
  "sources": [{"title": "...", "url": "https://..."}]     # opsional
}

Mini-markdown: paragraf dipisah baris kosong; baris diawali "- " = bullet;
**tebal**; [teks](url) = link.

Skrip ini menulis blog/<slug>.html, menambah/memperbarui kartu di blog/index.html
(terbaru di atas), dan menambah URL ke sitemap.xml. Aman dijalankan berulang.
"""
import html, json, re, sys
from datetime import date as _date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.konigautodetailing.com"
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
WA = "https://wa.me/62881080578712?text="


def tanggal_id(iso):
    d = _date.fromisoformat(iso)
    return f"{d.day} {BULAN[d.month - 1]} {d.year}"


def inline(text):
    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)

    def link(m):
        label, url = m.group(1), m.group(2)
        ext = url.startswith("http") and "konigautodetailing.com" not in url
        attrs = ' target="_blank" rel="noopener"' if ext else ""
        return f'<a href="{html.escape(url)}"{attrs}>{label}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)


def md(body):
    out = []
    for block in re.split(r"\n\s*\n", (body or "").strip()):
        lines = [l for l in block.split("\n") if l.strip()]
        if not lines:
            continue
        if all(re.match(r"\s*[-•]\s+", l) for l in lines):
            items = "".join("\n    <li>" + inline(re.sub(r"^\s*[-•]\s+", "", l)) + "</li>" for l in lines)
            out.append(f"  <ul>{items}\n  </ul>")
        else:
            out.append("  <p>" + "<br/>".join(inline(l) for l in lines) + "</p>")
    return "\n".join(out)


def build_article(a):
    slug, d = a["slug"], a["date"]
    parts = [
        '<article class="page-inner article">',
        '  <a href="/blog" class="nav-back">← Semua artikel</a>',
        f'  <span class="eyebrow" style="margin-top:20px">Artikel · {tanggal_id(d)}</span>',
        f'  <h1 class="page-title art-title">{inline(a["title"])}</h1>',
        '  <p class="byline">Oleh Bernhard, KONÏG Auto Detailing · detailer bersertifikasi SONAX &amp; CarPro</p>',
        "",
    ]
    if a.get("intro"):
        parts += [md(a["intro"]), ""]
    for s in a.get("sections", []):
        if s.get("heading"):
            parts.append(f'  <h2>{inline(s["heading"])}</h2>')
        parts += [md(s.get("body", "")), ""]
    cta = a.get("cta") or {}
    wa_text = "Halo KONÏG, saya baca artikel \"" + a["title"][:80] + "\" dan mau konsultasi"
    from urllib.parse import quote
    parts += [
        '  <div class="art-cta">',
        f'    <h2 style="margin-top:0">{inline(cta.get("heading") or "Konsultasi di KONÏG Auto Detailing")}</h2>',
        md(cta.get("body") or "KONÏG ada di Ruko Downtown Drive, Jl. Scientia Blvd DDBLV No.027, Medang, Pagedangan, dekat dari Gading Serpong, BSD, dan sekitarnya. Pengerjaan ditangani langsung oleh detailer bersertifikasi SONAX dan CarPro. Buka Senin–Sabtu, 08.00–17.00 WIB."),
        '    <div class="cta-row" style="margin:18px 0 0">',
        f'      <a href="{WA}{quote(wa_text)}" target="_blank" class="btn-wa" onclick="trackEvent(\'blog_wa_click\')">💬 Konsultasi via WA</a>',
        '      <a href="/pricelist" class="btn-outline">Lihat Pricelist</a>',
        '      <a href="/booking" class="btn-maps">Booking Jadwal →</a>',
        "    </div>",
        "  </div>",
    ]
    src = a.get("sources") or []
    if src:
        links = ", ".join(f'<a href="{html.escape(x["url"])}" target="_blank" rel="noopener">{html.escape(x["title"])}</a>' for x in src)
        parts.append(f'\n  <p class="refs">Sumber: {links}.</p>')
    parts.append("</article>")
    return "\n".join(parts)


def head_meta(a):
    url = f"{BASE}/blog/{a['slug']}"
    title = a.get("seoTitle") or a["title"]
    desc = a["metaDescription"]
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": a["title"], "description": desc,
        "datePublished": a["date"], "dateModified": a.get("dateModified", a["date"]),
        "inLanguage": "id-ID", "mainEntityOfPage": url, "image": f"{BASE}/graphene-banner.png",
        "author": {"@type": "Person", "name": "Bernhard"},
        "publisher": {"@type": "Organization", "name": "KONÏG Auto Detailing",
                      "logo": {"@type": "ImageObject", "url": f"{BASE}/konig-logo.png"}},
    }
    e = lambda x: html.escape(x, quote=True)
    return "\n".join([
        f'<meta name="description" content="{e(desc)}"/>',
        f"  <title>{e(title)}</title>",
        f'  <link rel="canonical" href="{url}"/>',
        '  <meta property="og:type" content="article"/>',
        f'  <meta property="og:title" content="{e(title)}"/>',
        f'  <meta property="og:description" content="{e(desc)}"/>',
        f'  <meta property="og:url" content="{url}"/>',
        f'  <meta property="og:image" content="{BASE}/graphene-banner.png"/>',
        '  <link rel="icon" href="/favicon.ico"/>',
        '  <script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>",
    ])


def update_index(a):
    p = ROOT / "blog" / "index.html"
    s = p.read_text()
    start, end = "<!-- POSTS:START -->", "<!-- POSTS:END -->"
    i, j = s.index(start) + len(start), s.index(end)
    cards = re.findall(r'(  <a class="post-card" href="/blog/([^"]+)"[^>]*>.*?</a>)', s[i:j], re.S)
    keep = [(c, sl) for c, sl in cards if sl != a["slug"]]
    e = lambda x: html.escape(x, quote=False)
    new = (f'  <a class="post-card" href="/blog/{a["slug"]}" data-date="{a["date"]}">\n'
           f'    <div class="post-date">{tanggal_id(a["date"])}</div>\n'
           f'    <div class="post-title">{e(a["title"])}</div>\n'
           f'    <div class="post-desc">{e(a.get("excerpt") or a["metaDescription"])}</div>\n'
           f'  </a>')
    allc = [(a["date"], new)] + [(re.search(r'data-date="([\d-]+)"', c).group(1) if 'data-date' in c else "0000", c) for c, _ in keep]
    allc.sort(key=lambda x: x[0], reverse=True)
    s = s[:i] + "\n" + "\n".join(c for _, c in allc) + "\n  " + s[j:]
    p.write_text(s)


def update_sitemap(a):
    p = ROOT / "sitemap.xml"
    s = p.read_text()
    loc = f"{BASE}/blog/{a['slug']}"
    entry = f"  <url><loc>{loc}</loc><lastmod>{a.get('dateModified', a['date'])}</lastmod></url>\n"
    if f"<loc>{loc}</loc>" in s:
        s = re.sub(r"  <url><loc>" + re.escape(loc) + r"</loc>.*?</url>\n", entry, s)
    else:
        s = s.replace("</urlset>", entry + "</urlset>")
    p.write_text(s)


def main():
    a = json.loads(Path(sys.argv[1]).read_text())
    for k in ("slug", "title", "metaDescription", "date", "sections"):
        assert a.get(k), f"field wajib kosong: {k}"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a["slug"]), "slug harus huruf kecil/angka/tanda hubung"
    tpl = (ROOT / "tools" / "article-template.html").read_text()
    out = tpl.replace("{{HEAD_META}}", head_meta(a)).replace("{{ARTICLE}}", build_article(a))
    (ROOT / "blog" / f"{a['slug']}.html").write_text(out)
    update_index(a)
    update_sitemap(a)
    print(f"OK: blog/{a['slug']}.html  ->  {BASE}/blog/{a['slug']}")


if __name__ == "__main__":
    main()
