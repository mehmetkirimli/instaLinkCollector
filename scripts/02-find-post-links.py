from playwright.sync_api import sync_playwright
import time

PROFILE_URL = "https://www.instagram.com/goturkiye/"
TARGET_COUNT = 500 

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    # ÖNEMLİ: Daha önce kaydettiğin session dosyasını BURAYA ekliyoruz
    context = browser.new_context(
        storage_state="instagram_session.json", 
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()

    try:
        print("➡️ Profil açılıyor...")
        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=90000)
        
        # Sayfanın oturması için biraz bekle
        time.sleep(5)

        all_links = set()
        print("🔍 Linkler toplanıyor...")

        # 500 tane bulana kadar kaydır
        while len(all_links) < TARGET_COUNT:
            # Sayfadaki linkleri çek
            current_links = page.eval_on_selector_all(
                "a", 
                "elements => elements.map(el => el.href).filter(h => h.includes('/p/'))"
            )
            
            for link in current_links:
                all_links.add(link)
            
            print(f"✅ Toplam Benzersiz Link: {len(all_links)}")
            
            if len(all_links) >= TARGET_COUNT:
                break
            
            # Kaydırma işlemi
            page.mouse.wheel(0, 2000)
            time.sleep(3) # Instagram'ın yeni postları yüklemesi için süre tanı

            # Güvenlik Kontrolü: Eğer 100 linkte takılırsa session düşmüş olabilir
            if len(all_links) == 0:
                print("⚠️ Hiç link bulunamadı! Ekran görüntüsü alınıyor...")
                page.screenshot(path="hata_goruntusu.png")
                break

        # Dosyaya yazdır
        final_list = list(all_links)[:TARGET_COUNT]
        with open("post_links.txt", "w", encoding="utf-8") as f:
            for link in final_list:
                f.write(link + "\n")

        print(f"🏁 Bitti! {len(final_list)} link kaydedildi.")

    except Exception as e:
        print(f"❌ Bir hata oluştu: {e}")
        page.screenshot(path="kritik_hata.png")
    
    browser.close()