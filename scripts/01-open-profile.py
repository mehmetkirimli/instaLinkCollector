from playwright.sync_api import sync_playwright

PROFILE_URL = "https://www.instagram.com/visit.dubai/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=50)

    context = browser.new_context(viewport={"width": 1280, "height": 800})

    page = context.new_page()

    print("➡️ Profil açılıyor...")
    page.goto(PROFILE_URL, timeout=60000)

    page.wait_for_load_state("networkidle")

    print("✅ Profil açıldı, 10 saniye bekleniyor...")
    page.wait_for_timeout(10000)

    browser.close()
    print("🧨 Tarayıcı kapandı")
# Instagram profilini açan ve 10 saniye bekleyen Playwright betiği tamamlandı.