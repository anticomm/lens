import os
import time
import requests
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from telegram_cep import send_epey_image

def normalize_title(title):
    title = title.lower()
    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def get_driver():
    options = Options()
    options.add_argument("--headless")  # klasik headless
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def find_epey_link(product_name: str) -> str:
    api_key = os.environ["GOOGLE_API_KEY"]
    cse_id = os.environ["CSE_ID"]
    clean_title = normalize_title(product_name)
    query = f"{clean_title} epey"

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data:
        for item in data["items"]:
            link = item.get("link", "")
            if "epey.com" in link:
                return link
    print(f"⚠️ Epey linki bulunamadı: {product_name}")
    return None

def capture_epey_screenshot(epey_url: str, save_path="epey.png"):
    try:
        driver = get_driver()
        driver.get(epey_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        time.sleep(2)

        if "arama" in epey_url or "search" in epey_url or "arama-sonucu" in driver.page_source:
            print(f"⚠️ Sayfa arama sonucu içeriyor: {epey_url}")
            driver.quit()
            return None

        driver.save_screenshot(save_path)
        driver.quit()
        return save_path
    except Exception as e:
        print(f"⚠️ Epey ekran görüntüsü hatası: {e}")
        return None

def capture_epey_fallback(title: str, asin: str) -> str:
    try:
        driver = get_driver()
        driver.get("https://www.epey.com/arama/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search_input")))

        input_box = driver.find_element(By.ID, "search_input")
        input_box.clear()
        input_box.send_keys(title)
        input_box.submit()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".urunliste, .arama-sonucu")))
        time.sleep(2)

        fallback_path = f"epey_fallback_{asin}.png"
        driver.save_screenshot(fallback_path)
        driver.quit()
        return fallback_path
    except Exception as e:
        print(f"⚠️ Fallback ekran görüntüsü hatası: {e}")
        return None

def run_capture(product: dict):
    title = product["title"]
    asin = product.get("asin", "fallback")
    epey_url = find_epey_link(title)

    if epey_url:
        screenshot_path = capture_epey_screenshot(epey_url, save_path=f"epey_{asin}.png")
        if screenshot_path:
            send_epey_image(product, screenshot_path)
            return

    print(f"🔄 Epey linki bulunamadı, arama sayfasına geçiliyor: {title}")
    fallback_path = capture_epey_fallback(title, asin)
    if fallback_path:
        send_epey_image(product, fallback_path)
