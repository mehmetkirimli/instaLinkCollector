from pathlib import Path

# Hedef Instagram profili
PROFILE_URL = "https://www.instagram.com/visit.dubai/"

SESSION_FILE = "instagram_session.json"
POST_LINKS_FILE = "post_links.txt"

DESKTOP = Path.home() / "Desktop"
EXCEL_OUTPUT = str(DESKTOP / "visit_dubai_instagram_fotograflar.xlsx")
EXCEL_BACKUP = str(DESKTOP / "visit_dubai_instagram_fotograflar_YEDEK.xlsx")

# Profil kaydirma
SCROLL_DELAY_SEC = 5
MAX_EMPTY_ROUNDS = 4
BATCH_SAVE_EVERY = 100

# Export: 10 post paralel, batch arasi 3 sn bekleme
BATCH_SIZE = 10
BATCH_DELAY_SEC = 3
PAGE_LOAD_WAIT_SEC = 2

TARGET_POST_COUNT = None
