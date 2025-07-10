import os
import time
import requests
import psycopg2
import psycopg2.extras
from tqdm import tqdm

# Load API key from environment variable
API_KEY = os.getenv("NVD_API_KEY")
if not API_KEY:
    raise EnvironmentError("NVD_API_KEY environment variable is not set")

# Configuration
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
PAGE_SIZE = 2000
SLEEP_INTERVAL = 1  # Safe with API key
DB_CONFIG = {
    "dbname": "nvd_database", # Your database
    "user": "postgreadmin", # Database username
    "password": "password", # Change password
    "host": "localhost",
    "port": 5432
}

def get_cves(start_index):
    params = {
        "startIndex": start_index,
        "resultsPerPage": PAGE_SIZE
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
    conn = psycopg2.connect(**DB_CONFIG)
    start_index = 0

    print("[*] Fetching total number of CVEs...")
    first_page = get_cves(0)
    if not first_page:
        print("Failed to fetch initial page.")
        return

    total = first_page.get("totalResults", 0)
    print(f"[+] Total CVEs to fetch: {total}")

    # Save first page
    for item in tqdm(first_page.get("vulnerabilities", []), desc="Page 0"):
        save_to_db(conn, item)

    start_index += PAGE_SIZE

    while start_index < total:
        time.sleep(SLEEP_INTERVAL)
        data = get_cves(start_index)
        if not data:
            print(f"[!] Failed to fetch page at index {start_index}. Exiting.")
            break
        for item in tqdm(data.get("vulnerabilities", []), desc=f"Page {start_index // PAGE_SIZE}"):
            save_to_db(conn, item)
        start_index += PAGE_SIZE

    conn.close()
    print("[✓] Ingestion complete.")

if __name__ == "__main__":
    main()
