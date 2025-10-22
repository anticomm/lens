import os
import requests
import subprocess

def shorten_url(url):
    try:
        response = requests.get(f"https://is.gd/create.php?format=simple&url={url}")
        if response.status_code == 200:
            return response.text.strip()
    except Exception as e:
        print(f"❌ Link kısaltma hatası: {e}")
    return url  # fallback

def format_product_message(product):
    if not product.get("link") or product.get("link") == "#":
        print(f"❌ Telegram link eksik: {product.get('title')}")
        return ""
    title = product.get("title", "🛍️ Ürün adı bulunamadı")
    price = product.get("price", "Fiyat alınamadı")
    old_price = product.get("old_price", "")  # 👈 Yeni satır
    link = shorten_url(product.get("link", "#"))
    discount = product.get("discount", "")
    rating = product.get("rating", "")
    colors = product.get("colors", [])
    specs = product.get("specs", [])

    if "TL" not in price:
        price = f"{price} TL"
    if old_price and "TL" not in old_price:
        old_price = f"{old_price} TL"

    indirimbilgi = f"%{discount}" if discount and discount.isdigit() else ""
    stars = f"⭐ {rating}" if rating else ""
    renkler = ", ".join([c["color"] for c in colors]) if colors else ""
    teknik = "\n".join([f"▫️ {spec}" for spec in specs]) if specs else ""

    if old_price and old_price != price:
        fiyat_bilgisi = (
            f"🔻 *Eski fiyat:* *{old_price}*\n"
            f"💰 *Yeni fiyat:* *{price}*"
        )
    else:
        fiyat_bilgisi = f"💰 *{price}*"

    return (
        f"*{title}*\n"
        f"{indirimbilgi}  {stars}\n"
        f"{teknik}\n"
        f"{f'🎨 Renkler: {renkler}' if renkler else ''}\n"
        f"{fiyat_bilgisi}\n"
        f"🔗 [🔥🔥 FIRSATA GİT 🔥🔥]({link})"
    )

def send_message(product):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    create_product_page(product)
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    base_url = f"https://api.telegram.org/bot{token}"
    subprocess.run(["git", "-C", "urunlerim", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "-C", "urunlerim", "config", "user.email", "actions@github.com"], check=True)
    
    if not token or not chat_id:
        print("❌ BOT_TOKEN veya CHAT_ID tanımlı değil.")
        return

    message = format_product_message(product)
    image_url = product.get("image")

    try:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(f"{base_url}/sendMessage", data=payload)

        if response.status_code == 200:
            print(f"✅ Gönderildi: {product.get('title', 'Ürün')}")
        else:
            print(f"❌ Gönderim hatası: {product.get('title', 'Ürün')} → {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Telegram gönderim hatası: {e}")


# 👇 Epey ekran görüntüsü gönderimi
def send_epey_image(product, image_path):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    base_url = f"https://api.telegram.org/bot{token}"

    if not token or not chat_id:
        print("❌ BOT_TOKEN veya CHAT_ID tanımlı değil.")
        return

    title = product.get("title", "📷 Epey Görseli")
    caption = f"*{title}*\n📊 Epey karşılaştırması"
    try:
        with open(image_path, "rb") as img:
            files = {"photo": img}
            payload = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "Markdown"
            }
            response = requests.post(f"{base_url}/sendPhoto", data=payload, files=files)
        if response.status_code == 200:
            print(f"✅ Epey görseli gönderildi: {title}")
        else:
            print(f"❌ Epey görsel gönderim hatası: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Epey görsel gönderim hatası: {e}")

# 👇 Epey link fallback gönderimi
def send_epey_link(product, url):
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    base_url = f"https://api.telegram.org/bot{token}"

    if not token or not chat_id:
        print("❌ BOT_TOKEN veya CHAT_ID tanımlı değil.")
        return

    title = product.get("title", "🔗 Epey Linki")
    message = f"*{title}*\n🔗 [Epey karşılaştırması]({url})"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(f"{base_url}/sendMessage", data=payload)
        if response.status_code == 200:
            print(f"✅ Epey linki gönderildi: {title}")
        else:
            print(f"❌ Epey link gönderim hatası: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Epey link gönderim hatası: {e}")
def create_product_page(product):
    print("📦 Gelen ürün verisi:")
    print(product)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    URUNLERIM_PATH = os.path.join(BASE_DIR, "urunlerim")
    if not product.get("amazon_link") or product.get("amazon_link") == "#":
        print(f"❌ Amazon link eksik, HTML oluşturulmayacak: {product.get('title')}")
        return
    slug = product.get("slug", "urun")  # ✅ eksik olan satır
    title = product.get("title", "Ürün")
    price = product.get("price", "")
    old_price = product.get("old_price", "")
    rating = product.get("rating", "")
    specs = product.get("specs", [])
    image = product.get("image", "")
    link = shorten_url(product.get("amazon_link", "#"))
    update_category_page()
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    URUNLERIM_PATH = os.path.join(BASE_DIR, "urunlerim")
    urun_klasoru = os.path.join(URUNLERIM_PATH, "urun")
    teknik = "".join([f"<li>{spec}</li>" for spec in specs])
    fiyat_html = f"<p><del>{old_price}</del> → <strong>{price}</strong></p>" if old_price and old_price != price else f"<p><strong>{price}</strong></p>"

    html = f"""
    print("📄 HTML içeriği:")
    print(html)
    <!DOCTYPE html>
    <html lang="tr">
    <head>
      <meta charset="UTF-8">
      <title>{title}</title>
      <link rel="stylesheet" href="../style.css">
    </head>
    <body>
      <div class="urun-sayfa">
        <div class="reklam-banner">
          <p>🔔 En iyi fırsatları kaçırma! Reklam alanı buraya gelecek.</p>
        </div>
        <div class="urun-detay">
          <img src="{product.get('image', '')}" alt="{title}">
          <h1>{title}</h1>
          {fiyat_html}
          <p>⭐ {rating}</p>
          <ul>{teknik}</ul>
          <a class="firsat-btn" href="{link}" target="_blank">Fırsata Git</a>
        </div>
        <div class="bildirim-alani">
          <button onclick="alert('Bildirim isteğin alındı!')">🔔 Bildirim Al</button>
        </div>
      </div>
    </body>
    </html>
    """
try:
    # Ana repo için kimlik tanımı
    subprocess.run(["git", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)

    # HTML dosyasını yaz
    os.makedirs(os.path.join(URUNLERIM_PATH, "urun"), exist_ok=True)
    path = os.path.join(os.getcwd(), "urunlerim", "urun", f"{slug}.html")
    print(f"🧪 Dosya yazılacak yol: {path}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    relative_path = os.path.relpath(path, os.path.join(os.getcwd(), "urunlerim"))
    os.utime(path, None)
    print(f"📏 Dosya boyutu: {os.path.getsize(path)} bayt")
    print(f"✅ HTML sayfası oluşturuldu: {path}")
    print(f"📁 HTML dosyası tam yol: {path}")
except Exception as e:
    print(f"❌ HTML sayfası oluşturulamadı: {e}")

try:
    # Submodule için kimlik tanımı
    subprocess.run(["git", "-C", "urunlerim", "config", "user.name", "github-actions"], check=True)
    subprocess.run(["git", "-C", "urunlerim", "config", "user.email", "actions@github.com"], check=True)

    # Submodule güncellemesi
    subprocess.run(["git", "-C", "urunlerim", "fetch"], check=True)
    subprocess.run(["git", "-C", "urunlerim", "reset", "--hard", "origin/main"], check=True)
    subprocess.run(["git", "-C", "urunlerim", "update-index", "--no-assume-unchanged", relative_path], check=False)
    subprocess.run(["git", "-C", "urunlerim", "add", "-f", relative_path], check=True)
    subprocess.run(["git", "-C", "urunlerim", "status"], check=True)
    subprocess.run(["git", "-C", "urunlerim", "commit", "-m", "Yeni ürün sayfaları eklendi"], check=True)
    subprocess.run([
        "git", "-C", "urunlerim", "push",
        f"https://{os.getenv('SUBMODULE_TOKEN')}@github.com/anticomm/urunlerim.git",
        "HEAD:main"
    ], check=True)

    print("🚀 HTML dosyaları GitHub'a gönderildi.")

    # Ana repo güncellemesi (önce reset, sonra commit)
    subprocess.run(["git", "fetch"], check=True)
    subprocess.run(["git", "reset", "--hard", "origin/master"], check=True)
    subprocess.run(["git", "add", "urunlerim"], check=True)
    subprocess.run(["git", "commit", "-m", "Submodule güncellendi"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD:master"], check=True)
except Exception as e:
    print(f"❌ Git işlemi başarısız: {e}")
    
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

        html = f"""
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <title>Ürünler</title>
            <link rel="stylesheet" href="../style.css">
            <style>
              ul {{
                list-style: none;
                padding: 0;
              }}
              li {{
                margin: 10px 0;
              }}
              a {{
                text-decoration: none;
                color: #ff6600;
                font-weight: bold;
              }}
              a:hover {{
                text-decoration: underline;
              }}
              .container {{
                padding: 40px;
              }}
            </style>
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
