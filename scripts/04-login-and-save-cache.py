from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False) # Tarayıcıyı görerek işlem yapalım
    context = browser.new_context()
    page = context.new_page()

    print("🚀 Instagram'a gidiliyor... Lütfen manuel giriş yap!")
    page.goto("https://www.instagram.com/accounts/login/")
    
    # Sana giriş yapman için 30 saniye süre veriyorum
    # Giriş yapıp ana sayfayı gördüğünde bekle
    time.sleep(30) 

    # ŞİMDİ asıl önemli olan: Tüm session'ı (cookie + storage) kaydediyoruz
    context.storage_state(path="instagram_session.json")
    print("✅ Session başarıyla kaydedildi! Şimdi scraper'ı çalıştırabilirsin.")
    
    browser.close()