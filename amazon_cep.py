import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def normalize_title_for_epey(title):
    title = title.lower()
    title = re.sub(r"\(.*?\)", "", title)  # parantez içini sil
    title = re.sub(r"\d{2,4}[.,]?\d{0,2}\s*x\s*\d{2,4}[.,]?\d{0,2}", "", title)  # boyutları sil
    title = re.sub(r"\b(eos r|zoom|lens|lensi|objektif|siyah|renkli|motoru|görüntü|sabitleyici|kit|mm)\b", "", title)
    title = re.sub(r"[^\w\s\.\-]", "", title)  # sadece kelime, boşluk, nokta ve tire kalsın
    title = re.sub(r"\s+", " ", title).strip()
    return title

def get_epey_url_from_selenium(driver, title):
    try:
        normalized = normalize_title_for_epey(title)
        query_url = f"https://www.epey.com/arama/?q={normalized.replace(' ', '+')}"
        driver.get(query_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.listing-item a[href^='https://www.epey.com/lens/']"))
        )

        for link in driver.find_elements(By.CSS_SELECTOR, "div.listing-item a[href^='https://www.epey.com/lens/']"):
            href = link.get_attribute("href")
            if "/karsilastir/" not in href:
                print(f"✅ Epey ürün linki bulundu: {href}")
                return href

        print(f"⚠️ Ürün sayfası bulunamadı: {title}")
        return None

    except Exception as e:
        print(f"⚠️ Epey arama hatası: {title} → {e}")
        return None
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Selenium driver başlat
options = Options()
options.add_argument("--headless")  # arka planda çalıştır
driver_epey = webdriver.Chrome(options=options)

# Ürün listesi örnek
products = [
    {"title": "Canon Objektif RF 24-105 mm F4-7.1 STM zoom lensi EOS R siyah, 76,6 x 88,8 mm"},
    {"title": "Canon RF-S 10-18mm F4.5-6.3 IS STM Lens"}
]

for p in products:
    epey_url = get_epey_url_from_selenium(driver_epey, p["title"])
    if epey_url:
        print(f"📎 Link eklendi: {epey_url}")
        p["epey_url"] = epey_url
    else:
        print(f"🚫 Link bulunamadı: {p['title']}")
        p["epey_url"] = None

driver_epey.quit()

# Sonuçları yazdır
for p in products:
    print(f"\n🆕 Ürün: {p['title']}")
    print(f"🔗 Epey Linki: {p['epey_url'] or 'Bulunamadı'}")
