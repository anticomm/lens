import os
import subprocess
import requests
import json
from bs4 import BeautifulSoup
import time

# ---------------------------
# Helpers
# ---------------------------

def run(cmd, cwd=None, check=False):
    """Basit wrapper: komutu çalıştır, stdout/stderr'i yazdır."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"$ {' '.join(cmd)} (cwd={cwd})")
        if proc.stdout:
            print(proc.stdout.strip())
        if proc.stderr:
            print(proc.stderr.strip())
        if check and proc.returncode != 0:
            raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        print(f"‼️ Komut çalıştırılamadı: {' '.join(cmd)} → {e}")
        return 1, "", str(e)

def safe_git_push_submodule(repo_dir, repo_url, max_retries=2):
    """
    Submodule içinde güvenli bir şekilde push yapmaya çalışır.
    Hata olursa fetch+reset ile onarır ve force-with-lease ile yeniden dener.
    """
    attempt = 0
    while attempt <= max_retries:
        attempt += 1
        print(f"🔁 Submodule push denemesi {attempt}/{max_retries+1}...")
        code, out, err = run(["git", "push", repo_url, "HEAD:main"], cwd=repo_dir, check=False)
        if code == 0:
            print("✅ Submodule push başarılı (normal push).")
            return True

        # Eğer burada reddedilmişse, retry ile onarmaya çalış
        print("⚠️ Push reddedildi veya hata var. Onarım denenecek...")
        # Fetch + checkout main + reset --hard origin/main ile temizle
        run(["git", "fetch", "--all"], cwd=repo_dir, check=False)
        run(["git", "checkout", "main"], cwd=repo_dir, check=False)
        run(["git", "reset", "--hard", "origin/main"], cwd=repo_dir, check=False)

        # Eğer commit varsa tekrar commit et (commit mesaj aynı değilse ignore ediyor)
        run(["git", "add", "-A"], cwd=repo_dir, check=False)
        run(["git", "commit", "-m", "Auto-commit from CI (retry push)"], cwd=repo_dir, check=False)

        # force-with-lease push
        code2, out2, err2 = run(["git", "push", repo_url, "HEAD:main", "--force-with-lease"], cwd=repo_dir, check=False)
        if code2 == 0:
            print("✅ Submodule push başarılı (force-with-lease).")
            return True

        print("❌ Force-with-lease de başarısız oldu, bekleyip tekrar denenecek.")
        time.sleep(1)  # küçük bekleme
    print("❌ Tüm push denemeleri başarısız oldu.")
    return False

# ---------------------------
# Amazon scraping + HTML generation
# ---------------------------

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
<html lang="tr"><head><meta charset="UTF-8"><title>Elektronik Ürünler</title><link rel="stylesheet" href="../style.css"></head><body><div class="navbar"><ul><li><a href="/">Anasayfa</a></li><li><a href="index.html">Elektronik</a></li></ul></div><div class="container"><h1>📦 Elektronik Ürünler</h1><ul>{liste}</ul></div></body></html>"""
        with open(os.path.join(kategori_path, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        print("✅ Elektronik kategori sayfası güncellendi.")
    except Exception as e:
        print(f"❌ Kategori sayfası hatası: {e}")

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

# ---------------------------
# Yeni, dayanıklı process_product
# ---------------------------

def process_product(product):
    html, slug = generate_html(product)
    if not html.strip():
        print(f"❌ HTML boş: {slug}")
        return

    kategori_path = os.path.join("urunlerim", "Elektronik")
    os.makedirs(kategori_path, exist_ok=True)
    filename = f"{slug}.html"
    path = os.path.join(kategori_path, filename)
    relative_path = os.path.join("Elektronik", filename)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        os.utime(path, None)
        print(f"✅ Ürün sayfası oluşturuldu: {path}")
    except Exception as e:
        print(f"❌ HTML sayfası oluşturulamadı: {e}")
        return

    # Repo URL için token kontrolü
    submodule_token = os.getenv("SUBMODULE_TOKEN")
    repo_url = (
        f"https://{submodule_token}@github.com/anticomm/urunlerim.git"
        if submodule_token else "https://github.com/anticomm/urunlerim.git"
    )

    # Git kimliği ayarla (hata toleranslı)
    run(["git", "config", "user.name", "github-actions"], cwd="urunlerim")
    run(["git", "config", "user.email", "actions@github.com"], cwd="urunlerim")

    # İlk olarak submodule durumunu düzeltmeye çalış
    run(["git", "fetch", "--all"], cwd="urunlerim")
    run(["git", "checkout", "main"], cwd="urunlerim")
    run(["git", "reset", "--hard", "origin/main"], cwd="urunlerim")

    # Dosyayı ekle & commit
    run(["git", "add", relative_path], cwd="urunlerim")
    # commit hata verirse (örneğin zaten commit yok) devam et
    run(["git", "commit", "-m", f"{slug} ürünü eklendi"], cwd="urunlerim")

    # Önce normal push dene, değilse safe push logic uygula
    success = safe_git_push_submodule("urunlerim", repo_url, max_retries=2)
    if not success:
        print("❌ Submodule push tekrar denemelerinde başarısız. Detayları loglarda kontrol et.")
    else:
        print("🚀 Submodule push tamamlandı.")

# ---------------------------
# Site üretimi ve ana repo push
# ---------------------------

def generate_site(products):
    for product in products:
        process_product(product)

    update_category_page()

    try:
        run(["git", "config", "user.name", "github-actions"])
        run(["git", "config", "user.email", "actions@github.com"])
        run(["git", "add", "urunlerim"], check=False)

        has_changes = subprocess.call(["git", "diff", "--cached", "--quiet"]) != 0

        if has_changes:
            run(["git", "commit", "-m", "Submodule güncellendi"])
            gh_token = os.getenv("GH_TOKEN")
            if gh_token:
                repo_url = f"https://{gh_token}@github.com/anticomm/indirimsinyali.git"
                print("🔐 GH_TOKEN bulundu, ana repo push yapılıyor...")
                run(["git", "push",]()
