"""Adim 3: Post fotograflarini 10'ar 10'ar paralel al, Excel'e yaz."""
import asyncio
import shutil
import sys
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright

from config import (
    BATCH_DELAY_SEC,
    BATCH_SIZE,
    EXCEL_BACKUP,
    EXCEL_OUTPUT,
    PAGE_LOAD_WAIT_SEC,
    POST_LINKS_FILE,
    PROFILE_URL,
    SESSION_FILE,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRAPE_JS = """() => {
    const meta = (p) => document.querySelector(`meta[property='${p}']`)?.content || "";
    const mediaType = meta("og:type");
    const isVideo = mediaType.includes("video") || !!document.querySelector("video");
    return {
        image_url: meta("og:image"),
        description: meta("og:description"),
        media_type: isVideo ? "Video" : "Fotograf",
    };
}"""


def profile_username() -> str:
    return PROFILE_URL.rstrip("/").split("/")[-1]


def read_post_links() -> list[str]:
    path = Path(POST_LINKS_FILE)
    if not path.exists():
        raise FileNotFoundError(f"Once collect_links.py calistir: {POST_LINKS_FILE}")
    user = profile_username()
    links = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and f"/{user}/" in line
    ]
    if not links:
        raise ValueError(f"{POST_LINKS_FILE} icinde {user} linki yok.")
    return links


def load_existing_rows() -> list[dict]:
    path = Path(EXCEL_OUTPUT)
    if not path.exists():
        return []
    return pd.read_excel(path).to_dict(orient="records")


def backup_excel() -> None:
    src = Path(EXCEL_OUTPUT)
    if src.exists():
        shutil.copy2(src, EXCEL_BACKUP)
        print(f"Yedek: {EXCEL_BACKUP}")


def save_excel(rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    target = Path(EXCEL_OUTPUT)
    temp = target.with_suffix(".tmp.xlsx")

    try:
        df.to_excel(temp, index=False)
        temp.replace(target)
    except PermissionError:
        fallback = target.with_name(f"{target.stem}_guncel{target.suffix}")
        df.to_excel(fallback, index=False)
        print(f"  UYARI: Excel acik, {fallback} dosyasina yazildi.", flush=True)


async def scrape_one(context, url: str) -> dict:
    page = await context.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(PAGE_LOAD_WAIT_SEC)
        data = await page.evaluate(SCRAPE_JS)
        return {
            "Post Linki": url,
            "Fotograf Linki": data["image_url"],
            "Aciklama": data["description"],
            "Tur": data["media_type"],
        }
    except Exception as exc:
        print(f"  Hata ({url}): {exc}", flush=True)
        return {
            "Post Linki": url,
            "Fotograf Linki": "",
            "Aciklama": "",
            "Tur": "",
        }
    finally:
        try:
            await page.close()
        except Exception:
            pass


async def scrape_batch(context, urls: list[str]) -> list[dict]:
    return list(await asyncio.gather(*(scrape_one(context, url) for url in urls), return_exceptions=False))


BROWSER_RESTART_EVERY = 50  # her 50 batch'te tarayiciyi yenile


def chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def run() -> None:
    all_links = read_post_links()
    rows = load_existing_rows()
    done = {str(r["Post Linki"]).strip() for r in rows if r.get("Post Linki")}
    pending = [url for url in all_links if url not in done]

    backup_excel()

    print(f"Profil: {PROFILE_URL}")
    print(f"Toplam: {len(all_links)} | Excel'de: {len(done)} | Kalan: {len(pending)}")
    print(f"Mod: {BATCH_SIZE} post paralel, batch arasi {BATCH_DELAY_SEC} sn")
    print(f"Excel: {EXCEL_OUTPUT}")

    if not pending:
        print("Tum postlar zaten Excel'de.")
        return

    context_kwargs = {"viewport": {"width": 1280, "height": 800}}
    session_path = Path(SESSION_FILE)
    if session_path.exists():
        context_kwargs["storage_state"] = str(session_path)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(**context_kwargs)

        processed = 0
        batch_index = 0
        for batch in chunks(pending, BATCH_SIZE):
            batch_index += 1
            if batch_index > 1 and (batch_index - 1) % BROWSER_RESTART_EVERY == 0:
                print("  Tarayici yenileniyor...", flush=True)
                await context.close()
                await browser.close()
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(**context_kwargs)

            batch_num = processed // BATCH_SIZE + 1
            total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE
            start = len(done) + processed + 1
            end = min(len(done) + processed + len(batch), len(all_links))
            print(f"\nBatch {batch_num}/{total_batches} | post {start}-{end}/{len(all_links)}", flush=True)

            try:
                results = await scrape_batch(context, batch)
            except Exception as exc:
                print(f"  Batch hatasi: {exc} — kaydedilip tarayici yenileniyor", flush=True)
                save_excel(rows)
                await context.close()
                await browser.close()
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(**context_kwargs)
                results = await scrape_batch(context, batch)

            rows.extend(results)
            processed += len(batch)

            ok = sum(1 for r in results if r.get("Fotograf Linki"))
            print(f"  -> {ok}/{len(batch)} OK | toplam Excel: {len(rows)}", flush=True)
            save_excel(rows)

            if processed < len(pending):
                await asyncio.sleep(BATCH_DELAY_SEC)

        await browser.close()

    ok_total = sum(1 for r in rows if r.get("Fotograf Linki"))
    print(f"\nBitti. {ok_total}/{len(rows)} fotograf linki Excel'de.")
    print(f"Excel: {EXCEL_OUTPUT}")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
