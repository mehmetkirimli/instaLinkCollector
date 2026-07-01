from playwright.sync_api import sync_playwright
import time

POST_LINKS_FILE = "post_links.txt"
MAX_POST = 3   # test için

def read_post_links(path, limit):
    links = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            link = line.strip()
            if link:
                links.append(link)
            if len(links) >= limit:
                break
    return links


print("🚀 ADIM 4 başladı: Post detail test (META TAG yöntemi)")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=50)

    context = browser.new_context(
        storage_state="instagram_session.json",
        viewport={"width": 1280, "height": 800}
    )

    page = context.new_page()
    post_links = read_post_links(POST_LINKS_FILE, MAX_POST)

    print(f"🔗 Test edilecek post sayısı: {len(post_links)}")

    for idx, post_url in enumerate(post_links, start=1):
        print("\n" + "=" * 60)
        print(f"📌 POST {idx}")
        print(f"🔗 URL: {post_url}")

        page.goto(post_url, timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # =========================
        # META TAG OKUMA
        # =========================
        def get_meta(property_name):
            locator = page.locator(f"meta[property='{property_name}']")
            if locator.count() > 0:
                return locator.first.get_attribute("content")
            return "YOK"

        description = get_meta("og:description")
        image_url = get_meta("og:image")
        media_type = get_meta("og:type")
        publish_time = get_meta("article:published_time")

        print("📝 og:description:", description)
        print("🖼️ og:image:", image_url)
        print("🎥 og:type:", media_type)
        print("📅 published_time:", publish_time)

        time.sleep(2)

    browser.close()

print("\n🏁 ADIM 4 test bitti (META)")
