import os
import time
import re
import requests
import feedparser
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID", "").strip()
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
SEEN_FILE = "posted_videos.txt"

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen(video_id):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(video_id + "\n")

def get_description(entry):
    desc = ""
    if hasattr(entry, "summary") and entry.summary:
        desc = entry.summary
    elif hasattr(entry, "media_description") and entry.media_description:
        desc = entry.media_description
    desc = re.sub(r"<[^>]+>", "", desc).strip()
    if not desc:
        desc = "কোনো ডেসক্রিপশন দেওয়া হয়নি।"
    if len(desc) > 800:
        desc = desc[:800].rstrip() + "..."
    return desc

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    response = requests.post(url, json=payload, timeout=20)
    return response.ok, response.text

def main():
    if not BOT_TOKEN or not CHANNEL_ID or not YOUTUBE_CHANNEL_ID:
        print("ত্রুটি: .env ফাইলে BOT_TOKEN, CHANNEL_ID অথবা YOUTUBE_CHANNEL_ID বসানো হয়নি।")
        return

    seen_videos = load_seen()
    print("YouTube to Telegram Auto Publisher চালু হয়েছে...")

    while True:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                for entry in reversed(feed.entries):
                    video_id = getattr(entry, "yt_videoid", None) or entry.link
                    if video_id not in seen_videos:
                        title = getattr(entry, "title", "নতুন ভিডিও").strip()
                        link = getattr(entry, "link", "").strip()
                        description = get_description(entry)
                        message = (
                            f"🎬 নতুন ভিডিও আপলোড হয়েছে!\n\n"
                            f"📌 টাইটেল: {title}\n\n"
                            f"📝 ডেসক্রিপশন:\n{description}\n\n"
                            f"🔗 ভিডিও লিংক: {link}"
                        )
                        ok, resp = send_to_telegram(message)
                        if ok:
                            save_seen(video_id)
                            seen_videos.add(video_id)
                            print(f"পোস্ট সফল হয়েছে: {title}")
                        else:
                            print(f"টেলিগ্রামে পাঠাতে সমস্যা হয়েছে: {resp}")
        except Exception as err:
            print(f"চেক করার সময় সমস্যা হয়েছে: {err}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
