import os
import subprocess
import requests
import json
import time
import random
from bs4 import BeautifulSoup
from collections import defaultdict

# ---------- Helperler ----------
def safe_text_from_tag(tag):
    if not tag:
        return None
    try:
        if hasattr(tag, "get_text"):
            t = tag.get_text(strip=True)
        else:
            t = tag.get("content") if tag.get("content") else None
        if not t or not t.strip():
            return None
        # bazı placeholder'ları filtrele
        tl = t.strip()
        if tl.lower() in ("amazon.com.tr", "ürün adı", "title"):
            return None
        return tl
    except Exception:
        return None

# ---------- Amazon veri çekme (geliştirilmiş) ----------
def get_amazon_data(asin, retries=3):
    url = f"https://www.amazon.com.tr/dp/{asin}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            print(f"[AMZ] {asin} status={resp.status_code} attempt={attempt}")
            if resp.status_code != 200:
                time.sleep(1 + random.random())
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # 1) primary selector
            title = safe_text_from_tag(soup.find("span", {"id": "productTitle"}))

            # 2) alternatif: meta og:title / meta name=title
            if not title:
                meta = soup.find("meta", {"property": "og:title"}) or soup.find("meta", {"name": "title"})
                if meta and meta.get("content"):
                    title = safe_text_from_tag(meta)

            # 3) alternatif: page <title>
            if not title and soup.title:
                title = safe_text_from_tag(soup.title)

            if title:
                print(f"[AMZ] Başlık bulundu: {asin} -> {title}")
            else:
                print(f"[AMZ] Başlık bulunamadı (henüz): {asin} attempt={attempt}")

            # Görsel çıkarma (mevcut mantığı güvenli hale getir)
            img_url = ""
            img_tag = soup.find("img", {"id": "landingImage"})
            if img_tag and img_tag.get("src"):
                img_url = img_tag["src"]
            else:
                dyn = soup.find("img", {"data-a-dynamic-image": True})
                if dyn:
                    try:
                        raw = dyn["data-a-dynamic-image"]
                        urls = list(json.loads(raw).keys())
                        if urls:
                            img_url = urls[0]
                    except Exception:
                        pass
                if not img_url:
                    sel = soup.select_one("img[src*='images-na.ssl-images-amazon.com']")
                    if sel and sel.get("src"):
                        img_url = sel["src"]
                    else:
                        old = soup.find("img", {"data-old-hires": True})
                        if old and old.get("data-old-hires"):
                            img_url = old["data-old-hires"]

            return title, img_url if img_url else ""
        except Exception as e:
            print(f"❌ Amazon verisi alınamadı: {asin} → {e} attempt={attempt}")
            time.sleep(1 + random.random())
    # tüm denemeler başarısızsa None döndür (ASIN fallback yok)
    return None, ""

def shorten_url(url):
    return url  # Şimdilik doğrudan geçiyoruz

# ---------- Kategori sayfası güncelle ----------
def update_category_page():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        URUNLERIM_PATH = os.path.join(BASE_DIR, "urunlerim")
        urun_klasoru = os.path.join(URUNLERIM_PATH, "urun")
        os.makedirs(urun_klasoru, exist_ok=True)
        html_dosyalar = [f for f in os.listdir(urun_klasoru) if f.endswith(".html") and f != "index.html"]

        liste = ""
        for dosya in sorted(html_dosyalar):
            slug = dosya.replace(".html", "")
            liste += f'<li><a href="{dosya}">{slug.replace("-", " ").title()}</a></li>\n'

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Ürünler</title>
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <div class="navbar">
      <ul>
        <li><a href="/">Anasayfa</a></li>
        <li><a href="index.html">Tüm Ürünler</a></li>
      </ul>
    </div>
    <div class="container">
      <h1>📦 Yayındaki Ürünler</h1>
      <ul>
        {liste}
      </ul>
    </div>
</body>
</html>
"""
        with open(os.path.join(urun_klasoru, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Kategori sayfası güncellendi.")
    except Exception as e:
        print(f"❌ Kategori sayfası hatası: {e}")

# ---------- HTML üretme ----------
def generate_html(product):
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    slug = product.get("slug", "urun")
    title = product.get("title", "")  # boşsa caller atlayacak
    price = product.get("price", "")
    old_price = product.get("old_price", "")
    rating = product.get("rating", "")
    specs = product.get("specs", [])
    image = product.get("image", "")
    link = shorten_url(product.get("amazon_link", "#"))
    asin = product.get("asin", slug)
    date = product.get("date", "")

    specs_html = "".join([f"<li>{spec}</li>" for spec in specs])
    fiyat_html = (
        f"<p><del>{old_price}</del> → <strong>{price}</strong></p>"
        if old_price and old_price != price
        else f"<p><strong>{price}</strong></p>"
    )

    # Güvenli formatlama: eksik anahtar format hatası yaratmasın
    data = defaultdict(str, {
        "title": title,
        "image": image,
        "price_html": fiyat_html,
        "specs_html": specs_html,
        "rating": rating,
        "link": link,
        "asin": asin,
        "date": date
    })

    html = template.format_map(data)
    return html, slug

# ---------- Ürün işleme ----------
def process_product(product):
    # DEBUG: process başında product içeriğini göster
    print(f"[PRE-PROCESS] slug={product.get('slug')} asin={product.get('asin')} title={repr(product.get('title'))} keys={list(product.keys())}")

    if not product.get("title"):
        print(f"[SKIP] HTML oluşturulmadı çünkü title yok -> {product.get('asin')}")
        return

    html, slug = generate_html(product)

    # DEBUG: html ön izlemesi ve başlık kontrolü
    contains_title = product.get("title") in html if product.get("title") else False
    print(f"[PRE-WRITE] slug={slug} title={repr(product.get('title'))} html_contains_title={contains_title}")
    if not contains_title:
        debug_path = os.path.join(os.getcwd(), f"debug_{slug}.html")
        with open(debug_path, "w", encoding="utf-8") as dbg:
            dbg.write(html)
        print(f"[DEBUG] Başlık html içinde bulunamadı, debug dosyası oluşturuldu: {debug_path}")

    URUNLERIM_PATH = os.path.join(os.getcwd(), "urunlerim")
    os.makedirs(os.path.join(URUNLERIM_PATH, "urun"), exist_ok=True)
    path = os.path.join(URUNLERIM_PATH, "urun", f"{slug}.html")
    relative_path = os.path.relpath(path, URUNLERIM_PATH)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        os.utime(path, None)
        print(f"✅ HTML sayfası oluşturuldu: {path}")
    except Exception as e:
        print(f"❌ HTML sayfası oluşturulamadı: {e}")
        return

    try:
        # Submodule için kimlik ayarı ve push
        subprocess.run(["git", "-C", "urunlerim", "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "-C", "urunlerim", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "-C", "urunlerim", "fetch", "--all"], check=True)
        subprocess.run(["git", "-C", "urunlerim", "reset", "--hard", "origin/main"], check=True)
        subprocess.run(["git", "-C", "urunlerim", "clean", "-fd"], check=True)
        subprocess.run(["git", "-C", "urunlerim", "add", "-f", relative_path], check=True)
        subprocess.run(["git", "-C", "urunlerim", "add", "-f", "urun/index.html"], check=True)
        # commit çalışmazsa hata verecek; bunu yakalayıp logluyoruz
        subprocess.run(["git", "-C", "urunlerim", "commit", "-m", "Yeni ürün sayfaları eklendi"], check=True)
        subprocess.run([
            "git", "-C", "urunlerim", "push",
            f"https://{os.getenv('SUBMODULE_TOKEN')}@github.com/anticomm/urunlerim.git",
            "HEAD:main"
        ], check=True)
        print("🚀 HTML dosyaları GitHub'a gönderildi.")

        # Ana repo için kimlik ayarı ve submodule commit
        subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "fetch"], check=True)
        subprocess.run(["git", "reset", "--hard", "origin/master"], check=True)
        subprocess.run(["git", "add", "urunlerim"], check=True)
        subprocess.run(["git", "commit", "-m", "Submodule güncellendi"], check=True)
        subprocess.run(["git", "push", "origin", "HEAD:master"], check=True)

    except Exception as e:
        print(f"❌ Git işlemi başarısız: {e}")

# ---------- Main ----------
def main():
    products = []
    send_file = "send_products.txt"
    if not os.path.exists(send_file):
        print(f"❌ {send_file} bulunamadı.")
        return

    with open(send_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            print(f"[READ send_products] {line}")
            if " | " in line:
                asin, price = line.split(" | ", 1)
                asin = asin.strip()
                price = price.strip()
                title, image_url = get_amazon_data(asin)

                # DEBUG: scraper sonrası durum
                print(f"[SCRAPER] {asin} -> title={repr(title)} image={image_url[:120]!r}")

                # Başlık yoksa atla (ASIN fallback yapılmıyor)
                if not title:
                    print(f"‼️ Başlık alınamadı, atlanıyor: {asin}")
                    continue

                if not image_url:
                    print(f"⚠️ Görsel bulunamadı: {asin}")

                print(f"🖼️ {asin} → {image_url}")
                print(f"📦 {asin} → {title}")

                products.append({
                    "asin": asin,
                    "slug": asin,
                    "title": title,
                    "price": price,
                    "amazon_link": f"https://www.amazon.com.tr/dp/{asin}",
                    "image": image_url
                })

    for product in products:
        process_product(product)

    update_category_page()

if __name__ == "__main__":
    main()
