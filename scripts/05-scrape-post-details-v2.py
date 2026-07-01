from playwright.sync_api import sync_playwright
import time
import re
import pandas as pd

# Ayarlar
POST_LINKS_FILE = "post_links.txt"
SESSION_FILE = "instagram_session.json"
MAX_POST = 10 # Test için 10 adet

def parse_stats(description):
    """Metin içinden sayıları (Beğeni, Yorum) ayıklar"""
    likes, comments = "0", "0"
    if description:
        # Örn: "4,116 Likes, 39 Comments"
        match = re.search(r'([\d.,KMB]+)\s+Likes,\s+([\d.,KMB]+)\s+Comments', description)
        if match:
            likes = match.group(1).replace(',', '').replace('.', '')
            comments = match.group(2).replace(',', '').replace('.', '')
    return likes, comments

def start_scraping():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=600)
        context = browser.new_context(storage_state=SESSION_FILE)
        page = context.new_page()

        with open(POST_LINKS_FILE, "r") as f:
            links = [line.strip() for line in f if line.strip()][:MAX_POST]

        for idx, url in enumerate(links, start=1):
            print(f"🔎 [{idx}] İşleniyor: {url}")
            try:
                page.goto(url, wait_until="commit", timeout=60000)
                time.sleep(5) # Sayfanın render olması için bekleme

                # JS ile sayfadan tüm verileri cımbızla alıyoruz
                data = page.evaluate("""() => {
                    const getM = (p) => document.querySelector(`meta[property='${p}']`)?.content || "";
                    const videoTag = document.querySelector('video');
                    
                    // Alternatif tarih bulma (time etiketi)
                    const timeTag = document.querySelector('time')?.getAttribute('datetime') || "";
                    
                    return {
                        desc: getM('og:description'),
                        type: getM('og:type'),
                        is_video: !!videoTag || getM('og:type').includes('video'),
                        time: timeTag || getM('article:published_time')
                    }
                }""")

                likes, comments = parse_stats(data['desc'])
                is_v = data['is_video']
                tur = "Video" if is_v else "Fotoğraf"

                # --- SENİN 11 KOLONLU ŞABLONUN ---
                row = {
                    "GO Türkiye İçerik Adı / Açıklaması": data['desc'].split("-")[1].strip() if "-" in data['desc'] else data['desc'],
                    "İçerik Linki": url,
                    "İçerik Tarihi": data['time'],
                    "İçerik Türü (Fotoğraf, Video)": tur,
                    "Fotoğraf Beğeni Etkileşim": likes if not is_v else "",
                    "Fotoğraf Yorum Etkileşim": comments if not is_v else "",
                    "Fotoğraf Yeniden Gönderim Etkileşim": "", # Meta tag'de bu bilgi yok
                    "Video Beğeni Etkileşim": likes if is_v else "",
                    "Video Yorum Etkileşim": comments if is_v else "",
                    "Video Yeniden Gönderim Etkileşim": "", # Meta tag'de bu bilgi yok
                    "Video İzlenme Etkileşim": "" # Login olup elementten çekilmeli
                }
                
                results.append(row)
                print(f"✅ Bitti -> Tür: {tur} | Tarih: {data['time']} | L: {likes} | C: {comments}")

            except Exception as e:
                print(f"❌ Hata: {url} -> {str(e)[:40]}")
                continue

        browser.close()

    if results:
        # Excel'e basıyoruz
        df = pd.DataFrame(results)
        df.to_excel("Instagram_8000_Analiz_V1.xlsx", index=False)
        print(f"\n🏁 İşlem tamam! 11 kolonluk dosya hazır birader.")

if __name__ == "__main__":
    start_scraping()