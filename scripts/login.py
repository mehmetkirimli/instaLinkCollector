"""Adım 1: Tarayıcıda Instagram'a giriş yap, oturumu kaydet."""
from playwright.sync_api import sync_playwright
import time

from config import SESSION_FILE

LOGIN_WAIT_SEC = 60

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("Instagram açılıyor. Lütfen giriş yap.")
    page.goto("https://www.instagram.com/accounts/login/")
    time.sleep(LOGIN_WAIT_SEC)

    context.storage_state(path=SESSION_FILE)
    print(f"Oturum kaydedildi: {SESSION_FILE}")
    browser.close()
