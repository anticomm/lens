import os
import json
import time
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram_cep import send_message, send_epey_image

def get_epey_search_url(title):
    base = "https://www.epey.com/arama/?q="
    return base + title.replace(" ", "+")

def capture_epey_screenshot(driver, title, save_path="epey.png"):
    try:
        url = get_epey_search_url(title)
        driver.get(url)
        time.sleep(2)
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
    if products_to_send:
        driver_epey = get_driver()  # Epey için ayrı driver

        for p in products_to_send:
            send_message(p)  # Amazon mesajı + görseli

            epey_image = capture_epey_screenshot(driver_epey, p["title"])
            if epey_image:
                send_epey_image(p, epey_image)

        driver_epey.quit()
        save_sent_data(sent_data)
        print(f"📁 Dosya güncellendi: {len(products_to_send)} ürün eklendi/güncellendi.")
    else:
        print("⚠️ Yeni veya indirimli ürün bulunamadı.")

if __name__ == "__main__":
    run()
