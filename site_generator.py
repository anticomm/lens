import os
import subprocess
from collections import defaultdict

URUNLERIM_DIR = "urunlerim"

def shorten_url(url):
    return url

def update_category_page():
    try:
        urun_klasoru = os.path.join(URUNLERIM_DIR, "urun")
        os.makedirs(urun_klasoru, exist_ok=True)
        html_dosyalar = [f for f in os.listdir(urun_klasoru) if f.endswith(".html") and f != "index.html"]

        liste = ""
        for dosya in sorted(html_dosyalar):
            slug = dosya.replace(".html", "")
            liste += f'<li><a href="{dosya}">{slug.replace("-", " ").title()}</a></li>\n'

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Ürünler</title><link rel="stylesheet" href="../style.css"></head>
<body>
<div class="navbar"><ul><li><a href="/">Anasayfa</a></li><li><a href="index.html">Tüm Ürünler</a></li></ul></div>
<div class="container"><h1>📦 Yayındaki Ürünler</h1><ul>{liste}</ul></div>
</body></html>
"""
        with open(os.path.join(urun_klasoru, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Kategori sayfası güncellendi.")
    except Exception as e:
        print(f"❌ Kategori sayfası hatası: {e}")

def generate_html(product):
    try:
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
    except Exception as e:
        raise RuntimeError(f"Template açılamadı: {e}")

    slug = product.get("slug", product.get("asin", "urun"))
    title = product.get("title", "")
    price = product.get("price", "")
    old_price = product.get("old_price", "")
    rating = product.get("rating", "")
    specs = product.get("specs", [])
    image = product.get("image", "")
    link = shorten_url(product.get("amazon_link", "#"))
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
        "asin": slug,
        "date": date
    })

    html = template.format_map(data)
    return html, slug

def process_product(product):
    print(f"[HTML] {product.get('asin')} → {product.get('title')}")
    if not product.get("title"):
        print(f"[SKIP] Başlık yok → {product.get('asin')}")
        return False

    html, slug = generate_html(product)
    urun_path = os.path.join(URUNLERIM_DIR, "urun", f"{slug}.html")
    os.makedirs(os.path.dirname(urun_path), exist_ok=True)

    try:
        with open(urun_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ HTML oluşturuldu: {urun_path}")
    except Exception as e:
        print(f"❌ HTML yazma hatası: {e}")
        return False

    try:
        subprocess.run(["git", "-C", URUNLERIM_DIR, "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "-C", URUNLERIM_DIR, "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "-C", URUNLERIM_DIR, "fetch", "--all"], check=True)
        subprocess.run(["git", "-C", URUNLERIM_DIR, "reset", "--hard", "origin/main"], check=True)
        subprocess.run(["git", "-C", URUNLERIM_DIR, "clean", "-fd"], check=True)
        subprocess.run(["git", "-C", URUNLERIM_DIR, "add", "-f", f"urun/{slug}.html"], check=True)
        subprocess.run(["git", "-C", URUNLERIM_DIR, "add", "-f", "urun/index.html"], check=True)
        subprocess.run(["git", "-C", URUNLERIM_DIR, "commit", "-m", "Yeni ürün sayfaları eklendi"], check=True)
        subprocess.run([
            "git", "-C", URUNLERIM_DIR, "push",
            f"https://{os.getenv('SUBMODULE_TOKEN')}@github.com/anticomm/urunlerim.git",
            "HEAD:main"
        ], check=True)
        print("🚀 GitHub Pages güncellendi.")
    except Exception as e:
        print(f"❌ Git işlemi hatası: {e}")
        return False

    return True

def generate_site(products):
    processed = 0
    for product in products:
        if process_product(product):
            processed += 1
    update_category_page()
    print(f"📁 Dosya güncellendi: {processed} ürün eklendi/güncellendi.")
