from playwright.sync_api import sync_playwright
import time
import os

PROFILE_URL = "https://www.instagram.com/goturkiye/"
FINAL_GOAL = 8000  # Nihai hedefimiz
BATCH_SAVE_COUNT = 250 # Her 250 postta bir "Ben buradayım" diyecek
POST_LINKS_FILE = "post_links.txt"

def load_existing_links():
    if os.path.exists(POST_LINKS_FILE):
        with open(POST_LINKS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=100)
    context = browser.new_context(
        storage_state="instagram_session.json", 
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()

    try:
        print(f"🚀 8000 post hedefiyle yolculuk başlıyor...")
        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(5)

        all_links = load_existing_links()
        print(f"📂 Başlangıçta dosyada bulunan link: {len(all_links)}")

        consecutive_no_new_links = 0
        
        while len(all_links) < FINAL_GOAL:
            # Sayfadaki linkleri topla
            current_links = page.eval_on_selector_all(
                "a", 
                "elements => elements.map(el => el.href).filter(h => h.includes('/p/'))"
            )
            
            before_count = len(all_links)
            for link in current_links:
                all_links.add(link)
            
            # Yeni link gelip gelmediğini kontrol et
            if len(all_links) == before_count:
                consecutive_no_new_links += 1
            else:
                consecutive_no_new_links = 0
            
            # Her BATCH_SAVE_COUNT postta bir dosyaya yaz (Yedekleme)
            if len(all_links) % BATCH_SAVE_COUNT < 10 and len(all_links) > before_count:
                with open(POST_LINKS_FILE, "w", encoding="utf-8") as f:
                    for l in sorted(list(all_links)):
                        f.write(l + "\n")
                print(f"💾 {len(all_links)} linke ulaşıldı ve yedeklendi. Kısa bir mola...")
                time.sleep(10) # Instagram'ı uyutalım

            print(f"🔄 İlerleme: {len(all_links)} / {FINAL_GOAL}")

            # 8000'e ulaştıysak dur
            if len(all_links) >= FINAL_GOAL:
                break
            
            # Eğer 15 kaydırma boyunca yeni link gelmezse muhtemelen Instagram blokladı
            if consecutive_no_new_links > 15:
                print("⚠️ Yeni içerik yüklenemiyor. Instagram limit koymuş olabilir.")
                break

            # Kaydır
            page.mouse.wheel(0, 3000)
            time.sleep(3) # Yeni postların gelmesi için bekleme

        # Final Kayıt
        with open(POST_LINKS_FILE, "w", encoding="utf-8") as f:
            for link in sorted(list(all_links)):
                f.write(link + "\n")
        
        print(f"🏁 İşlem bitti! Toplam {len(all_links)} link toplandı.")

    except Exception as e:
        print(f"❌ Kritik hata: {e}")
    
    browser.close()