import os
import subprocess
import requests
import json
from bs4 import BeautifulSoup
import shutil

# =====================================================
# 🔹 SUBMODULE SELF-HEALING MEKANİZMASI
# =====================================================
def ensure_clean_submodule():
    print("🔍 Submodule bütünlüğü kontrol ediliyor...")
    try:
        result = subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            check=False, capture_output=True, text=True
        )
        if (
            "not our ref" in result.stderr
            or "Direct fetching of that commit failed" in result.stderr
        ):
            print("⚠️ Submodule bozuk. Yeniden oluşturuluyor...")
            subprocess.run(["git", "rm", "-f", "urunlerim"], check=False)
            shutil.rmtree(".git/modules/urunlerim", ignore_errors=True)
            shutil.rmtree("urunlerim", ignore_errors=True)
            subprocess.run(
                ["git", "submodule", "add", "https://github.com/anticomm/urunlerim.git", "urunlerim"],
                check=True
            )
            subprocess.run(["git", "submodule", "update", "--init", "--recursive"], check=True)
            subprocess.run(["git", "add", ".gitmodules", "urunlerim"], check=False)
            subprocess.run(["git", "commit", "-m", "Submodule otomatik olarak yeniden eklendi"], check=False)
            subprocess.run(["git", "push", "origin", "master"], check=False)
            print("✅ Submodule başarıyla yeniden kuruldu.")
        else:
            print("✅ Submodule sağlam, devam ediliyor.")
    except Exception as e:
        print(f"❌ Submodule kontrolü sırasında hata oluştu: {e}")

# =====================================================
# 🔹 AMAZON VERİ ÇEKME
# =====================================================
def get_amazon_data(asin):
    url = f"https://www.amazon.com.tr/dp/{asin}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "tr-TR,tr;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.find("span", {"id": "productTitle"})
        title = title_tag.get_text(strip=True) if title_tag else asin
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

# =====================================================
# 🔹 HTML OLUŞTURMA VE KATEGORİ SAYFASI
# =====================================================
def shorten_url(url):
    return url

def update_category_page():
    try:
        kategori_path = os.path.join("urunlerim", "Elektronik")
        os.makedirs(kategori_path, exist_ok=True)
        html_dosyalar = [f for f in os.listdir(kategori_path) if f.endswith(".html") and f != "index.html"]
        liste = ""
        for dosya in sorted(html_dosyalar):
            slug = dosya.replace(".html", "")
            liste += f'<li><a href="{dosya}">{slug.replace("-", " ").title()}</a></li>\n'
        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Elektronik Ürünler</title>
<link rel="stylesheet" href="../style.css">
</head>
<body>
<div class="navbar">
<ul>
<li><a href="/">Anasayfa</a></li>
<li><a href="index.html">Elektronik</a></li>
</ul>
</div>
<div class="container">
<h1>📦 Elektronik Ürünler</h1>
<ul>{liste}</ul>
</div>
</body>
</html>"""
        with open(os.path.join(kategori_path, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Elektronik kategori sayfası güncellendi.")
    except Exception as e:
        print(f"❌ Kategori sayfası hatası: {e}")

# =====================================================
# 🔹 ÜRÜN SAYFASI OLUŞTURMA
# =====================================================
def generate_html(product):
    try:
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print("❌ template.html dosyası bulunamadı. HTML oluşturulamadı.")
        return "", product.get("slug", "urun")
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
            subprocess.run(["git", "-C", "urunlerim", "add", relative_path], check=True)
        has_changes = subprocess.call(["git", "-C", "urunlerim", "diff", "--cached", "--quiet"]) != 0
        if has_changes:
            subprocess.run(["git", "-C", "urunlerim", "commit", "-m", f"{slug} ürünü eklendi"], check=True)
            subprocess.run(["git", "-C", "urunlerim", "push", repo_url, "main", "--force-with-lease"], check=False)
            print("🚀 Submodule push tamamlandı.")
        else:
            print("⚠️ Submodule için commit edilecek değişiklik yok.")
    except Exception as e:
        print(f"❌ Submodule Git işlemi başarısız: {e}")
        return

    # 🔁 lens repo’su submodule referansını güncellesin
    try:
        subprocess.run(["git", "add", "urunlerim"], check=True)
        has_submodule_change = subprocess.call(["git", "diff", "--cached", "--quiet"]) != 0
        if has_submodule_change:
            subprocess.run(["git", "commit", "-m", f"{slug} submodule referansı güncellendi"], check=True)
            subprocess.run(["git", "push", "origin", "master"], check=True)
            print("🔁 Ana repo submodule referansı güncellendi.")
        else:
            print("⚠️ Ana repo için submodule değişikliği yok.")
    except Exception as e:
        print(f"❌ Ana repo submodule güncelleme hatası: {e}")

# =====================================================
# 🔹 ANA İŞLEV
# =====================================================
def generate_site(products):
    ensure_clean_submodule()  # ✅ önce submodule sağlam mı kontrol et

    for product in products:
        process_product(product)
    update_category_page()

    try:
        subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", "urunlerim"], check=True)

        has_changes = subprocess.call(["git", "diff", "--cached", "--quiet"]) != 0

        if has_changes:
            subprocess.run(["git", "commit", "-m", "Submodule güncellendi"], check=True)
            gh_token = os.getenv("GH_TOKEN")
            if gh_token:
                repo_url = f"https://{gh_token}@github.com/anticomm/lens.git"
                subprocess.run(["git", "push", repo_url, "HEAD:master"], check=True)
                print("🚀 Ana repo push tamamlandı.")
            else:
                print("⚠️ GH_TOKEN tanımlı değil. Ana repo push atlanıyor.")
        else:
            print("⚠️ Ana repo için commit edilecek değişiklik yok.")
    except Exception as e:
        print(f"❌ Ana repo Git işlemi başarısız: {e}")
