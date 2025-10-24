import os
import subprocess
import json
from collections import defaultdict

# ---------- Ayarlar ----------
PRODUCTS_JSON = "products.json"
SEND_FILE = "send_products.txt"
URUNLERIM_DIR = "urunlerim"

# ---------- Yardımcılar ----------
def load_products_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"❌ products.json okunamadı: {e}")
        return {}

def shorten_url(url):
    return url

# ---------- Kategori sayfası ----------
def update_category_page():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        URUNLERIM_PATH = os.path.join(BASE_DIR, URUNLERIM_DIR)
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

# ---------- HTML üretimi ----------
def generate_html_from_template(product, template_path="template.html"):
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    except Exception as e:
        raise RuntimeError(f"Template açılamadı: {e}")

    slug = product.get("slug", "urun")
    title = product.get("title", "")
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

# ---------- HTML oluştur + Git push ----------
def process_product_and_push(product, urunlerim_dir=URUNLERIM_DIR, push=True):
    print(f"[PRE-PROCESS] slug={product.get('slug')} asin={product.get('asin')} title={repr(product.get('title'))}")

    if not product.get("title"):
        print(f"[SKIP] HTML oluşturulmadı çünkü title yok → {product.get('asin')}")
        return False

    html, slug = generate_html_from_template(product)

    contains_title = product.get("title") in html if product.get("title") else False
    print(f"[PRE-WRITE] slug={slug} title={repr(product.get('title'))} html_contains_title={contains_title}")
    if not contains_title:
        debug_path = os.path.join(os.getcwd(), f"debug_{slug}.html")
        with open(debug_path, "w", encoding="utf-8") as dbg:
            dbg.write(html)
        print(f"[DEBUG] Başlık HTML içinde bulunamadı → {debug_path}")

    URUNLERIM_PATH = os.path.join(os.getcwd(), urunlerim_dir)
    os.makedirs(os.path.join(URUNLERIM_PATH, "urun"), exist_ok=True)
    path = os.path.join(URUNLERIM_PATH, "urun", f"{slug}.html")
    relative_path = os.path.relpath(path, URUNLERIM_PATH)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ HTML sayfası oluşturuldu: {path}")
    except Exception as e:
        print(f"❌ HTML yazma hatası: {e}")
        return False

    if push:
        try:
            subprocess.run(["git", "-C", urunlerim_dir, "config", "user.name", "github-actions"], check=True)
            subprocess.run(["git", "-C", urunlerim_dir, "config", "user.email", "actions@github.com"], check=True)
            subprocess.run(["git", "-C", urunlerim_dir, "fetch", "--all"], check=True)
            subprocess.run(["git", "-C", urunlerim_dir, "reset", "--hard", "origin/main"], check=True)
            subprocess.run(["git", "-C", urunlerim_dir, "clean", "-fd"], check=True)
            subprocess.run(["git", "-C", urunlerim_dir, "add", "-f", relative_path], check=True)
            subprocess.run(["git", "-C", urunlerim_dir, "add", "-f", "urun/index.html"], check=True)
            subprocess.run(["git", "-C", urunlerim_dir, "commit", "-m", "Yeni ürün sayfaları eklendi"], check=True)
            subprocess.run([
                "git", "-C", urunlerim_dir, "push",
                f"https://{os.getenv('SUBMODULE_TOKEN')}@github.com/anticomm/urunlerim.git",
                "HEAD:main"
            ], check=True)
            print("🚀 HTML dosyaları GitHub'a gönderildi.")
        except Exception as e:
            print(f"❌ Git işlemi başarısız: {e}")
            return False

    return True

# ---------- Main ----------
def main():
    meta = load_products_json(PRODUCTS_JSON)
    if meta:
        print(f"✅ {PRODUCTS_JSON} yüklendi, {len(meta)} ürün bulundu.")
    else:
        print(f"ℹ️ {PRODUCTS_JSON} bulunamadı veya boş. send_products.txt ile devam edilecek.")

    if not os.path.exists(SEND_FILE):
        print(f"❌ {SEND_FILE} bulunamadı.")
        return

    products_to_process = []
    with open(SEND_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or " | " not in line:
                continue
            asin, price = line.split(" | ", 1)
            asin = asin.strip()
            price = price.strip()

            if asin in meta:
                m = meta[asin]
                products_to_process.append({
                    "asin": asin,
                    "slug": asin,
                    "title": m.get("title", ""),
                    "price": price or m.get("price", ""),
                    "old_price": m.get("old_price", ""),
                    "amazon_link": m.get("amazon_link", f"https://www.amazon.com.tr/dp/{asin}"),
                    "image": m.get("image", ""),
                    "rating": m.get("rating", ""),
                    "specs": m.get("specs", []),
                    "date": m.get("date", "")
                })
            else:
                print(f"⚠️ Metadata yok: {asin} → HTML oluşturulmayacak")

    processed =
