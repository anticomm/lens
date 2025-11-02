import os
import subprocess
import json
from bs4 import BeautifulSoup
import requests

def safe_run(cmd, cwd=None, check=True):
    print("🔹", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout)
    if result.stderr.strip():
        print(result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Komut başarısız: {' '.join(cmd)}\n{result.stderr}")
    return result

def setup_submodule():
    print("🔧 Submodule kontrol ediliyor...")
    safe_run(["git", "submodule", "sync", "--recursive"], check=False)
    safe_run(["git", "submodule", "update", "--init", "--recursive"], check=False)
    safe_run(["git", "-C", "urunlerim", "fetch", "origin"], check=False)
    safe_run(["git", "-C", "urunlerim", "checkout", "main"], check=False)
    safe_run(["git", "-C", "urunlerim", "pull", "--rebase", "origin", "main"], check=False)

def get_amazon_data(asin):
    url = f"https://www.amazon.com.tr/dp/{asin}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "tr-TR,tr;q=0.9"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("span", {"id": "productTitle"})
        img = soup.find("img", {"id": "landingImage"})
        title = title.get_text(strip=True) if title else asin
        img_url = img["src"] if img and img.get("src") else ""
        return title, img_url
    except Exception as e:
        print("❌ Amazon hatası:", e)
        return asin, ""

def generate_html(product):
    title = product.get("title")
    img = product.get("image")
    asin = product.get("asin")
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>{title}</title></head>
<body><h1>{title}</h1><img src="{img}" alt="{title}" width="300"></body></html>"""
    return html, asin

def process_product(product):
    html, asin = generate_html(product)
    dest_dir = os.path.join("urunlerim", "Elektronik")
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, f"{asin}.html")
    with open(dest_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Ürün yazıldı: {dest_file}")

def push_submodule():
    print("🚀 Submodule push başlatılıyor...")
    gh_token = os.getenv("GH_TOKEN")
    if not gh_token:
        print("⚠️ GH_TOKEN tanımlı değil, push atlanıyor.")
        return

    repo_url = f"https://{gh_token}@github.com/anticomm/urunlerim.git"

    try:
        safe_run(["git", "-C", "urunlerim", "config", "user.name", "github-actions"])
        safe_run(["git", "-C", "urunlerim", "config", "user.email", "actions@github.com"])
        safe_run(["git", "-C", "urunlerim", "add", "Elektronik"])
        diff = subprocess.call(["git", "-C", "urunlerim", "diff", "--cached", "--quiet"])
        if diff != 0:
            safe_run(["git", "-C", "urunlerim", "commit", "-m", "Yeni ürünler eklendi"])
            safe_run(["git", "-C", "urunlerim", "push", repo_url, "HEAD:main", "--force-with-lease"])
        else:
            print("⚠️ Değişiklik yok, submodule push atlanıyor.")
    except Exception as e:
        print(f"❌ Submodule Git işlemi başarısız: {e}")

def update_main_repo():
    print("🧩 Ana repo güncelleniyor...")
    try:
        safe_run(["git", "add", "urunlerim"])
        diff = subprocess.call(["git", "diff", "--cached", "--quiet"])
        if diff != 0:
            safe_run(["git", "commit", "-m", "Submodule güncellendi"])
            gh_token = os.getenv("GH_TOKEN")
            repo_url = f"https://{gh_token}@github.com/anticomm/lens.git" if gh_token else "origin"
            safe_run(["git", "push", repo_url, "HEAD:main"])
        else:
            print("⚠️ Ana repoda değişiklik yok, push atlanıyor.")
    except Exception as e:
        print(f"❌ Ana repo Git işlemi başarısız: {e}")

# === ÇALIŞMA AKIŞI ===
setup_submodule()

# Örnek ürünler
products = [
    {"asin": "B07XTS8QXK", "title": "Ütü 1", "image": "https://example.com/img1.jpg"},
    {"asin": "B00C3Y2IC4", "title": "Ütü 2", "image": "https://example.com/img2.jpg"},
]

for p in products:
    process_product(p)

push_submodule()
update_main_repo()
