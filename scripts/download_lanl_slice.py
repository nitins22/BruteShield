"""
Download empirical slice of LANL auth.txt.gz using parallel range requests.
"""

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "lanl")
os.makedirs(DATA_DIR, exist_ok=True)
OUT_PATH = os.path.join(DATA_DIR, "auth.txt.gz")

TOTAL_BYTES = 100 * 1024 * 1024  # 100 MB slice
CHUNK_SIZE = 10 * 1024 * 1024    # 10 MB per chunk
NUM_WORKERS = 4


def get_token():
    url = "https://csr.lanl.gov/data-fence/token?email=researcher@bruteshield.edu&usage=academic_research"
    resp = requests.get(url, timeout=30)
    token = resp.text.strip()
    return token


def fetch_chunk(args):
    idx, start, end, url = args
    headers = {"Range": f"bytes={start}-{end}"}
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=60)
            if resp.status_code in (200, 206):
                return idx, resp.content
        except Exception as e:
            time.sleep(2)
    raise RuntimeError(f"Failed to fetch chunk {idx} ({start}-{end})")


def main():
    print(f"Acquiring LANL CSR access token...")
    token = get_token()
    url = f"https://csr.lanl.gov/data-fence/{token}/cyber1/auth.txt.gz"
    print(f"Token acquired: {token}")

    chunk_args = []
    idx = 0
    start = 0
    while start < TOTAL_BYTES:
        end = min(start + CHUNK_SIZE - 1, TOTAL_BYTES - 1)
        chunk_args.append((idx, start, end, url))
        start += CHUNK_SIZE
        idx += 1

    print(f"Starting parallel download of {len(chunk_args)} chunks ({TOTAL_BYTES / (1024*1024):.1f} MB) using {NUM_WORKERS} workers...")
    t0 = time.time()
    chunks = {}

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        for idx, content in executor.map(fetch_chunk, chunk_args):
            chunks[idx] = content
            print(f"  Chunk {idx+1}/{len(chunk_args)} downloaded ({len(content)/(1024*1024):.2f} MB)")

    dt = time.time() - t0
    print(f"All chunks downloaded in {dt:.1f}s ({TOTAL_BYTES / (1024*1024) / dt:.2f} MB/s). Assembling to {OUT_PATH}...")

    with open(OUT_PATH, "wb") as f_out:
        for i in range(len(chunk_args)):
            f_out.write(chunks[i])

    print(f"Saved {os.path.getsize(OUT_PATH)} bytes to {OUT_PATH}")


if __name__ == "__main__":
    main()
