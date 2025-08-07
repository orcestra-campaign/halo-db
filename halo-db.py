# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beautifulsoup4",
#     "feedparser",
#     "requests",
# ]
# ///
import argparse
import json
import pathlib
import re

import feedparser
import requests
from bs4 import BeautifulSoup


class HaloDB:
    def __init__(self):
        self.url = "https://halo-db.pa.op.dlr.de"

        user_config = pathlib.Path("~/.halodb").expanduser()
        with open(user_config, "r") as fp:
            credentials = json.loads(fp.read())

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            f"{self.url}/login",
            data=credentials,
            headers=headers,
            allow_redirects=False,
        )
        response.raise_for_status()

        self._cookie = response.headers.get("Set-Cookie").split(";")[0]

    def get(self, url, stream=False):
        headers = headers = {"Cookie": self._cookie}

        response = requests.get(url, headers=headers, stream=stream)
        response.raise_for_status()

        return response

    def download(self, url, path, chunk_size=1_048_576):
        response = self.get(url, stream=True)

        fp_part = path.with_suffix(".partial")
        with open(fp_part, "wb") as fp:
            for buf in response.iter_content(chunk_size=chunk_size):
                fp.write(buf)

        fp_part.rename(path)

    def get_datasets(self, mission_id):
        feed_url = rf"{self.url}/mission/{mission_id}?format=rss"
        feed = feedparser.parse(feed_url)

        yield from (self.extract_dataset_metadata(entry) for entry in feed.entries)

    def extract_dataset_metadata(self, entry):
        # Extract dataset id and filename from title
        match = re.search(r"#(\d+) \| (.*)", entry["title"])
        dataset_id = match.group(1)
        filename = match.group(2)

        # Parse release table for file link and release number
        ret = self.get(f"{self.url}/dataset/{dataset_id}")
        soup = BeautifulSoup(ret.content, "html.parser")

        releases_div = soup.find("div", id="releases")
        for row in releases_div.find("table").find_all("tr")[1:]:
            cols = row.find_all(["td", "th"])

            release = cols[0].get_text().strip()

            link = cols[3].find("a")
            href = link["href"][3:] if link else None

            if href:
                break

        return {
            "dataset_url": entry["link"],
            "dataset_id": dataset_id,
            "filename": filename,
            "file_url": f"{self.url}/{href}",
            "release": release,
        }

    def downloads_all_datasets(self, mission_id):
        for ds in self.get_datasets(mission_id=mission_id):
            dataset_id = ds["dataset_id"]
            release = ds["release"]
            filename = ds["filename"]
            url = ds["file_url"]

            fp = pathlib.Path(
                f"HALO-DB_dataset{dataset_id}_release{release}_{filename}"
            )

            if fp.exists():
                print(f"Skip {fp}")
                continue

            print(f"Download {fp}")
            self.download(url, fp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="HALO Download Bot")
    parser.add_argument("-m", "--mission", default=141, help="Mission ID")
    args = parser.parse_args()

    halodb = HaloDB()
    halodb.downloads_all_datasets(mission_id=args.mission)
