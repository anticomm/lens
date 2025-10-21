import os
import requests
import subprocess

def format_product_message(product):
    title = product.get("title", "🛍️ Ürün adı bulunamadı")
    price = product.get("price", "Fiyat alınamadı")
    old_price = product.get("old_price", "")  # 👈 Yeni satır
    link = product.get("link", "#")
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
    create_product_page(product)
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    base_url = f"https://api.telegram.org/bot{token}"

    if not token or not chat_id:
        print("❌ BOT_TOKEN veya CHAT_ID tanımlı değil.")
        return

    message = format_product_message(product)
    image_url = product.get("image")

    try:
        if image_url and image_url.startswith("http"):
            payload = {
                "chat_id": chat_id,
                "photo": image_url,
                "caption": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(f"{base_url}/sendPhoto", data=payload)
        else:
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True  # 👈 virgül eklendi

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
    title = product.get("title", "Ürün")
    price = product.get("price", "")
    old_price = product.get("old_price", "")
    rating = product.get("rating", "")
    specs = product.get("specs", [])
    image = product.get("image", "")
    link = product.get("link", "#")
    slug = product.get("slug", "urun")  # 👈 Dosya adı için

    teknik = "".join([f"<li>{spec}</li>" for spec in specs])
    fiyat_html = f"<p><del>{old_price}</del> → <strong>{price}</strong></p>" if old_price and old_price != price else f"<p><strong>{price}</strong></p>"

    html = f"""
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
        os.makedirs("urunlerim/urun", exist_ok=True)  # 👈 klasör garantisi buraya
        path = f"urunlerim/urun/{slug}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"✅ HTML sayfası oluşturuldu: {path}")
    except Exception as e:
        print(f"❌ HTML sayfası oluşturulamadı: {e}")
    try:
        subprocess.run(["git", "-C", "urunlerim", "add", "."], check=True)
        subprocess.run(["git", "-C", "urunlerim", "commit", "-m", "Yeni ürün sayfaları eklendi"], check=True)
        subprocess.run([
            "git", "-C", "urunlerim", "push",
            f"https://{os.getenv('SUBMODULE_TOKEN')}@github.com/anticomm/urunlerim.git"
        ], check=True)
        print("🚀 HTML dosyaları GitHub'a gönderildi.")
    except Exception as e:
        print(f"❌ Git işlemi başarısız: {e}")
