"""
Populate the database by running all data ingestion scripts in order.

Usage:
    python populate.py
"""

import subprocess
import sys
import time

SCRIPTS = ["fetch_stocks.py", "fetch_news.py", "sentiment.py"]

def main():
    start = time.perf_counter()
    for script in SCRIPTS:
        print(f"\n=== Running {script} ===")
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"\n {script} failed. Aborting.")
            sys.exit(1)
    print("\n Database populated successfully.")
    print(f"Finished in {time.perf_counter() - start:.2f}s")


if __name__ == "__main__":
    main()