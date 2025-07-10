import os
import time
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from tqdm import tqdm

# -- CONFIGURATION --
API_KEY = os.getenv("NVD_API_KEY")
DB_CONFIG = {
    "dbname": "nvd_database", # Your database
    "user": "postgreadmin", # Database username
    "password": "password", # Change password
    "host": "localhost",
    "port": 5432
}
SYNC_FILE = "last_sync.txt"
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
PAGE_SIZE = 2000
SLEEP_INTERVAL = 1
# -------------------

def load_last_sync_time():
    if os.path.exists(SYNC_FILE):
        with open(SYNC_FILE, "r") as f:
            return datetime.fromisoformat(f.read().strip())
    else:
        return datetime.utcnow() - timedelta(hours=6)  # default fallback

def save_sync_time(dt):
    with open(SYNC_FILE, "w") as f:
        f.write(dt.isoformat())

def get_cves(start_index, start_time, end_time):
    params = {
        "startIndex": start_index,
        "resultsPerPage": PAGE_SIZE,
        "lastModStartDate": start_time.isoformat(timespec='milliseconds') + "Z",
        "lastModEndDate": end_time.isoformat(timespec='milliseconds') + "Z"
    }
    headers = {
        "apiKey": API_KEY
    }
    resp = requests.get(NVD_API_URL, params=params, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"[!] Error {resp.status_code}: {resp.text}")
        return None

def save_to_db(conn, cve_item):
    cve_id = cve_item["cve"]["id"]
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO cves (cve_id, full_json)
            VALUES (%s, %s)
            ON CONFLICT (cve_id) DO UPDATE SET
                full_json = EXCLUDED.full_json;
        """, (cve_id, psycopg2.extras.Json(cve_item)))
    conn.commit()

def main():
    if not API_KEY:
        raise EnvironmentError("NVD_API_KEY environment variable is not set.")

    conn = psycopg2.connect(**DB_CONFIG)

    start_time = load_last_sync_time()
    end_time = datetime.utcnow()

    print(f"[*] Syncing CVEs from {start_time} to {end_time}")
    start_index = 0

    first_page = get_cves(start_index, start_time, end_time)
    if not first_page:
        print("[!] Initial delta fetch failed.")
        return

    total = first_page.get("totalResults", 0)
    print(f"[+] Total updated CVEs: {total}")

    for item in tqdm(first_page.get("vulnerabilities", []), desc="Page 0"):
        save_to_db(conn, item)

    start_index += PAGE_SIZE

    while start_index < total:
        time.sleep(SLEEP_INTERVAL)
        page = get_cves(start_index, start_time, end_time)
        if not page:
            break
        for item in tqdm(page.get("vulnerabilities", []), desc=f"Page {start_index // PAGE_SIZE}"):
            save_to_db(conn, item)
        start_index += PAGE_SIZE

    save_sync_time(end_time)
    conn.close()
    print("[✓] Delta sync complete.")

if __name__ == "__main__":
    main()
