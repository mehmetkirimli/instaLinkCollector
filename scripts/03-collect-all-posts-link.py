from playwright.sync_api import sync_playwright
import time
import csv
from pathlib import Path

PROFILE_URL = "https://www.instagram.com/goturkiye/"
SESSION_DIR = Path("session")
OUTPUT_FILE = "post_links.csv"

SCROLL_DELAY = 3
MAX_EMPTY_ROUNDS = 4

print("🚀 Script başladı")

def main():
    all_links = set()
    empty_rounds = 0

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            slow_mo=50,
            viewport={"width": 1280, "height": 800},
            args=["--start-maximized"]
        )

        page = context.pages[0]
        print("➡️ Profile gidiliyor...")
        page.goto(PROFILE_URL, timeout=60000)
        time.sleep(5)

        while True:
            print("\n🔄 SCROLL")

            # 🔥 KRİTİK SATIR (senin çalışan mantığın)
            links = page.eval_on_selector_all(
                "a[href*='/p/'], a[href*='/reel/']",
                "els => els.map(e => e.href)"
            )

            before = len(all_links)
            all_links.update(links)
            after = len(all_links)
            new_count = after - before

            print(f"➕ Yeni eklenen: {new_count}")
            print(f"📊 Toplam benzersiz: {after}")

            if new_count == 0:
                empty_rounds += 1
                print(f"⚠️ Yeni veri yok ({empty_rounds}/{MAX_EMPTY_ROUNDS})")
            else:
                empty_rounds = 0

            if empty_rounds >= MAX_EMPTY_ROUNDS:
                print("🛑 Yeni post gelmiyor, bitiriliyor")
                break

            page.mouse.wheel(0, 4000)
            time.sleep(SCROLL_DELAY)

        context.close()

    save_csv(all_links)
    print(f"\n✅ TOPLAM POST LINK SAYISI: {len(all_links)}")
    print(f"📄 {OUTPUT_FILE} yazıldı")
    print("🏁 Script bitti")

def save_csv(links):
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["post_url"])
        for link in sorted(links):
            w.writerow([link])

if __name__ == "__main__":
    main()
