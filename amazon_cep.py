import os
import json
import time
import base64
import requests
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram_cep import send_message, send_epey_image
def normalize_title_for_epey(title):
    title = title.lower()
    title = re.sub(r"\(.*?\)", "", title)  # parantez içini sil
    title = re.sub(r"\d{2,4}[.,]?\d{0,2}\s*x\s*\d{2,4}[.,]?\d{0,2}", "", title)  # boyutları sil (virgül/nokta dahil)
    title = re.sub(r"\b(eos r|zoom|lens|lensi|objektif|siyah|renkli|motoru|görüntü|sabitleyici|mm|epey.com)\b", "", title)
    title = re.sub(r"[^\w\s\.\-]", "", title)  # sadece kelime, boşluk, nokta ve tire kalsın
    title = re.sub(r"\s+", " ", title).strip()
    return title


def get_epey_url_from_artado(title):
    import requests
    from bs4 import BeautifulSoup

    normalized = normalize_title_for_epey(title)
    query = f"{normalized} epey.com"
    url = f"https://www.artado.com/search?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36"
    }

    print(f"🔎 Artado araması: {query}")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.select("a.gs-title[href*='epey.com']"):
        href = a["href"]
        if href.startswith("https://www.epey.com/"):
            print(f"✅ Epey linki bulundu: {href}")
            return href
    print(f"⚠️ Epey linki bulunamadı: {title}")
    return None

def capture_epey_screenshot(driver, title_or_url, save_path="epey.png"):
    try:
        if title_or_url.startswith("https://www.epey.com/"):
            url = title_or_url
        else:
            normalized = normalize_title_for_epey(title_or_url)
            url = f"https://www.epey.com/arama/?q={normalized.replace(' ', '+')}"

        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        driver.save_screenshot(save_path)
        return save_path
    except Exception as e:
        print(f"⚠️ Epey ekran görüntüsü alınamadı: {e}")
        return None

URL = "https://www.amazon.com.tr/s?i=electronics&rh=n%3A13710137031%2Cp_36%3A-5000000%2Cp_123%3A359121%2Cp_n_g-101013615904111%3A68100078031%2Cp_98%3A21345978031%2Cp_n_condition-type%3A13818537031&dc&ds=v1%3A6sZpe%2FYE4bu2CESwIu9R1HeLmlpl8j6yDZ3GeYQEjJg"
COOKIE_FILE = "cookie_cep.json"
SENT_FILE = "send_products.txt"

def decode_cookie_from_env():
    cookie_b64 = os.getenv("COOKIE_B64")
    if not cookie_b64:
        print("❌ COOKIE_B64 bulunamadı.")
        return False
    try:
        decoded = base64.b64decode(cookie_b64)
        with open(COOKIE_FILE, "wb") as f:
            f.write(decoded)
        print("✅ Cookie dosyası oluşturuldu.")
        return True
    except Exception as e:
        print(f"❌ Cookie decode hatası: {e}")
        return False

def load_cookies(driver):
    if not os.path.exists(COOKIE_FILE):
        print("❌ Cookie dosyası eksik.")
        return
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    for cookie in cookies:
        try:
            driver.add_cookie({
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie.get("path", "/")
            })
        except Exception as e:
            print(f"⚠️ Cookie eklenemedi: {cookie.get('name')} → {e}")

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_used_price_from_item(item):
    try:
        container = item.find_element(
            By.XPATH,
            ".//span[contains(text(), 'Diğer satın alma seçenekleri')]/following::span[contains(text(), 'TL')][1]"
        )
        price = container.text.strip()
        return price
    except:
        return None

def get_used_price_from_detail(driver):
    try:
        container = driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'a-column') and .//span[contains(text(), 'İkinci El Ürün Satın Al:')]]"
        )
        price_element = container.find_element(By.CLASS_NAME, "offer-price")
        price = price_element.text.strip()
        return price
    except:
        return None

def get_final_price(driver, link):
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(link)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        price = get_used_price_from_detail(driver)
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return price
    except Exception as e:
        print(f"⚠️ Detay sayfa hatası: {e}")
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        return None

def load_sent_data():
    data = {}
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|", 1)
                if len(parts) == 2:
                    asin, price = parts
                    data[asin.strip()] = price.strip()
    return data

def save_sent_data(updated_data):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        for asin, price in updated_data.items():
            f.write(f"{asin} | {price}\n")
def run():
    if not decode_cookie_from_env():
        return

    driver = get_driver()
    driver.get(URL)
    time.sleep(2)
    load_cookies(driver)
    driver.get(URL)

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )
    except:
        print("⚠️ Sayfa yüklenemedi.")
        driver.quit()
        return

    driver.execute_script("""
      document.querySelectorAll("h5.a-carousel-heading").forEach(h => {
        let box = h.closest("div");
        if (box) box.remove();
      });
    """)

    items = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
    print(f"🔍 {len(items)} ürün bulundu.")
    products = []
    for item in items:
        try:
            if item.find_elements(By.XPATH, ".//span[contains(text(), 'Sponsorlu')]"):
                continue

            asin = item.get_attribute("data-asin")
            if not asin:
                continue

            title = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("alt").strip()
            link = item.find_element(By.CSS_SELECTOR, "a.a-link-normal").get_attribute("href")
            image = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")

            price = get_used_price_from_item(item)
            if not price:
                price = get_final_price(driver, link)

            if not price:
                continue

            products.append({
                "asin": asin,
                "title": title,
                "link": link,
                "image": image,
                "price": price
            })

        except Exception as e:
            print(f"⚠️ Ürün parse hatası: {e}")
            continue

    driver.quit()
    print(f"✅ {len(products)} ürün başarıyla alındı.")

    sent_data = load_sent_data()
    products_to_send = []

    for product in products:
        asin = product["asin"]
        price = product["price"].strip()

        if asin in sent_data:
            old_price = sent_data[asin]
            try:
                old_val = float(old_price.replace("TL", "").replace(".", "").replace(",", ".").strip())
                new_val = float(price.replace("TL", "").replace(".", "").replace(",", ".").strip())
            except:
                print(f"⚠️ Fiyat karşılaştırılamadı: {product['title']} → {old_price} → {price}")
                sent_data[asin] = price
                continue

            if new_val < old_val:
                print(f"📉 Fiyat düştü: {product['title']} → {old_price} → {price}")
                product["old_price"] = old_price
                products_to_send.append(product)
            else:
                print(f"⏩ Fiyat yükseldi veya aynı: {product['title']} → {old_price} → {price}")
            sent_data[asin] = price

        else:
            print(f"🆕 Yeni ürün: {product['title']}")
            products_to_send.append(product)
            sent_data[asin] = price

    if products_to_send:
        driver_epey = get_driver()  # Epey için ayrı driver

        for p in products_to_send:
            send_message(p)  # Amazon mesajı + görseli

            epey_url = get_epey_url_from_artado(p["title"])
            if epey_url:
                epey_image = capture_epey_screenshot(driver_epey, epey_url)
                if epey_image:
                    send_epey_image(p, epey_image)
            else:
                print(f"⚠️ Epey linki bulunamadı: {p['title']}")

        driver_epey.quit()
        save_sent_data(sent_data)
        print(f"📁 Dosya güncellendi: {len(products_to_send)} ürün eklendi/güncellendi.")
    else:
        print("⚠️ Yeni veya indirimli ürün bulunamadı.")

if __name__ == "__main__":
    run()
