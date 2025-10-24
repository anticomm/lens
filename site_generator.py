import os
import subprocess
import requests
import json
from bs4 import BeautifulSoup

def get_amazon_data(asin):
    url = f"https://www.amazon.com.tr/dp/{asin}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "tr-TR,tr;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Başlık
        title_tag = soup.find("span", {"id": "productTitle"})
        title = title_tag.get_text(strip=True) if title_tag else asin

        # Görsel
        img_url = ""
        img_tag = soup.find("img", {"id": "landingImage"})
        if img_tag and img_tag.get("src"):
            img_url = img_tag["src"]
        elif soup.find("img", {"data-a-dynamic-image": True}):
            raw = soup.find("img", {"data-a-dynamic-image": True})["data-a-dynamic-image"]
            urls = list(json.loads(raw).keys())
            if urls:
                img_url = urls[0]
        elif soup.select_one("img[src*='images-na.ssl-images-amazon.com']"):
            img_url = soup.select_one("img[src*='images-na.ssl-images-amazon.com']")["src"]
        elif soup.find("img", {"data-old-hires": True}):
            img_url = soup.find("img", {"data-old-hires": True})["data-old-hires"]

        return title, img_url
    except Exception as e:
        print(f"❌ Amazon verisi alınamadı: {asin} → {e}")
        return asin, ""

def shorten_url(url):
    return url  # Şimdilik doğrudan geçiyoruz, istersen bit.ly entegrasyonu ekleriz

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
<html lang="tr"><head><meta charset="UTF-8"><title>Ürünler</title><link rel="stylesheet" href="../style.css"></head><body><div class="navbar"><ul><li><a href="/">Anasayfa</a></li><li><a href="index.html">Tüm Ürünler</a></li></ul></div><div class="container"><h1>📦 Yayındaki Ürünler</h1><ul>{liste}</ul></div></body></html>"""
        with open(os.path.join(urun_klasoru, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Kategori sayfası güncellendi.")
    except Exception as e:
        print(f"❌ Kategori sayfası hatası: {e}")

def generate_html(product):
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    slug = product.get("slug", "urun")
    title = product.get("title", "Ürün")
    price = product.get("price", "")
    old_price = product.get("old_price", "")
    rating = product.get("rating", "")
    specs = product.get("specs", [])
    image = product.get("image", "")
    link = shorten_url(product.get("amazon_link", "#"))
    asin = slug
    date = product.get("date", "2025-10-24")

    specs_html = "".join([f"<li>{spec}</li>" for spec in specs])
    fiyat_html = (
        f"<p><del>{old_price}</del> → <strong>{price}</strong></p>"
        if old_price and old_price != price
        else f"<p><strong>{price}</strong></p>"
    )

    html = template.format(
        title=title,
        image=image,
        price_html=fiyat_html,
        specs_html=specs_html,
        rating=rating,
        link=link,
        asin=asin,
        date=date
    )

    return html, slug

def process_product(product):
    html, slug = generate_html(product)
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
        subprocess.run(["git", "-C", "urunlerim", "fetch"], check=True)
        subprocess.run(["git", "-C", "urunlerim", "reset", "--hard", "origin/main"], check=True)
        subprocess.run(["git", "-C", "urunlerim", "add", "-f", relative_path], check=True)
        subprocess.run(["git", "-C", "urunlerim", "add", "-f", "urun/index.html"], check=True)
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

def main():
    products = []
    with open("send_products.txt", "r", encoding="utf-8") as f:
        for line in f:
            if " | " in line:
                asin, price = line.strip().split(" | ")
                title, image_url = get_amazon_data(asin)

                if not image_url:
                    print(f"⚠️ Görsel bulunamadı: {asin}")
                if title == asin:
                    print(f"⚠️ Başlık bulunamadı: {asin}")

                print(f"🖼️ {asin} → {image_url}")
                print(f"📦 {asin} → {title}")

                products.append({
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
