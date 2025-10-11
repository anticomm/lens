import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from telegram_cep import send_epey_image

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def find_epey_link(product_name: str) -> str:
    api_key = os.environ["GOOGLE_API_KEY"]
    cse_id = os.environ["CSE_ID"]
    query = f"{product_name} epey"  # Sadece 'epey' kelimesi eklendi

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        return data["items"][0]["link"]
    else:
        print(f"⚠️ Epey linki bulunamadı: {product_name}")
        return None

def capture_epey_screenshot(epey_url: str, save_path="epey.png"):
    try:
        driver = get_driver()
        driver.get(epey_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        time.sleep(2)
        driver.save_screenshot(save_path)
        driver.quit()
        return save_path
    except Exception as e:
        print(f"⚠️ Epey ekran görüntüsü hatası: {e}")
        return None

def run_capture(product: dict):
    title = product["title"]
    epey_url = find_epey_link(title)
    if not epey_url:
        return
    screenshot_path = capture_epey_screenshot(epey_url)
    if screenshot_path:
        send_epey_image(product, screenshot_path)
