"""Adim 2: Profildeki post linklerini kaydirarak topla (yavas, sirayla)."""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import (
    BATCH_SAVE_EVERY,
    MAX_EMPTY_ROUNDS,
    POST_LINKS_FILE,
    PROFILE_URL,
    SCROLL_DELAY_SEC,
    SESSION_FILE,
    TARGET_POST_COUNT,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def profile_username() -> str:
    return PROFILE_URL.rstrip("/").split("/")[-1]


def load_existing_links() -> set[str]:
    path = Path(POST_LINKS_FILE)
    if not path.exists():
        return set()
    user = profile_username()
    links = {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    matching = {link for link in links if f"/{user}/" in link}
    if links and len(matching) != len(links):
        print(f"Eski profil linkleri atildi ({len(links) - len(matching)} adet).")
    return matching


def save_links(links: set[str]) -> None:
    user = profile_username()
    filtered = sorted(link for link in links if f"/{user}/" in link)
    Path(POST_LINKS_FILE).write_text(
        "\n".join(filtered) + ("\n" if filtered else ""),
        encoding="utf-8",
    )


def main() -> None:
    user = profile_username()
    all_links = load_existing_links()
    empty_rounds = 0

    print(f"Profil: {PROFILE_URL}")
    if all_links:
        print(f"Dosyada mevcut {user} linki: {len(all_links)}")

    session_path = Path(SESSION_FILE)
    context_kwargs = {"viewport": {"width": 1280, "height": 800}}
    if session_path.exists():
        context_kwargs["storage_state"] = str(session_path)
    else:
        print("Oturum dosyasi yok, public profil deneniyor.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=80)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()

        page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(6)

        while True:
            if TARGET_POST_COUNT and len(all_links) >= TARGET_POST_COUNT:
                break

            before = len(all_links)
            hrefs = page.eval_on_selector_all(
                "a[href*='/p/'], a[href*='/reel/']",
                "els => els.map(e => e.href)",
            )
            all_links.update(h for h in hrefs if f"/{user}/" in h)

            new_count = len(all_links) - before
            print(f"Toplam: {len(all_links)} (+{new_count})")

            if new_count == 0:
                empty_rounds += 1
                if empty_rounds >= MAX_EMPTY_ROUNDS:
                    print("Yeni post gelmiyor, bitiriliyor.")
                    break
            else:
                empty_rounds = 0
                if len(all_links) % BATCH_SAVE_EVERY < new_count:
                    save_links(all_links)
                    print(f"Yedek kaydedildi ({len(all_links)} link)")
                    time.sleep(8)

            page.mouse.wheel(0, 3500)
            time.sleep(SCROLL_DELAY_SEC)

        browser.close()

    if TARGET_POST_COUNT:
        all_links = set(sorted(all_links)[:TARGET_POST_COUNT])

    save_links(all_links)
    print(f"Bitti. {len(all_links)} post linki -> {POST_LINKS_FILE}")


if __name__ == "__main__":
    main()
