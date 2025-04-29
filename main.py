import json
import time
import random
from typing import Dict

import jmespath
from parsel import Selector
from nested_lookup import nested_lookup
from playwright.sync_api import sync_playwright

import io
import csv

def parse_thread(data: Dict) -> Dict:
    """Parse Twitter tweet JSON dataset for the most important fields"""
    result = jmespath.search(
        """{
        text: post.caption.text,
        published_on: post.taken_at,
        id: post.id,
        pk: post.pk,
        code: post.code,
        username: post.user.username,
        user_pic: post.user.profile_pic_url,
        user_verified: post.user.is_verified,
        user_pk: post.user.pk,
        user_id: post.user.id,
        has_audio: post.has_audio,
        reply_count: view_replies_cta_string,
        like_count: post.like_count,
        images: post.carousel_media[].image_versions2.candidates[1].url,
        image_count: post.carousel_media_count,
        videos: post.video_versions[].url
    }""",
        data,
    )
    result["videos"] = list(set(result["videos"] or []))
    if result["reply_count"] and type(result["reply_count"]) != int:
        result["reply_count"] = int(result["reply_count"].split(" ")[0])
    result[
        "url"
    ] = f"https://www.threads.net/@{result['username']}/post/{result['code']}"
    return result

# def analyze_emotions(threads: List[str]) -> str:
#     return ""

def find_datasets(hidden_datasets) -> dict:
     # find datasets that contain threads data
    for hidden_dataset in hidden_datasets:
        # skip loading datasets that clearly don't contain threads data
        if '"ScheduledServerJS"' not in hidden_dataset:
            continue
        if "thread_items" not in hidden_dataset:
            continue
        data = json.loads(hidden_dataset)
        # datasets are heavily nested, use nested_lookup to find 
        # the thread_items key for thread data
        thread_items = nested_lookup("thread_items", data)
        if not thread_items:
            continue
        # use our jmespath parser to reduce the dataset to the most important fields
        threads = [parse_thread(t) for thread in thread_items for t in thread]


        # wait to scrape
        # time_to_sleep = random.randint(2,4)
        # time.sleep(time_to_sleep)

        # treat main post and replies the same
        return threads

           
                # return {
                # # the first parsed thread is the main post:
                # "thread": threads[0],
                # # other threads are replies:
                # "replies": threads[1:],
                # }
    raise ValueError("could not find thread data in page")

def scroll_until(days_old):
    seconds_old = days_old * 86400



def scrape_thread(url: str) -> dict:
    """Scrape Threads post and replies from a given URL"""
    with sync_playwright() as pw:
        # start Playwright browser
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        # go to url and wait for the page to load
        page.goto(url)
        # wait for page to finish loading
        page.wait_for_selector("[data-pressable-container=true]")
        # find all hidden datasets
        selector = Selector(page.content())
        hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()

        # scroll until content is 1 month old

        landing_page_threads = find_datasets(hidden_datasets)
        
        if landing_page_threads[-1]["published_on"] is not None:
            published_time = landing_page_threads[-1]["published_on"]
            # TODO: compare current time and published time, keep scrolling
            # if they are less than a month apart
            # upload a function

            # TODO: create a different CSV for each thread scraped, then analyze with AI


        time.sleep(1)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_selector("[data-pressable-container=true]")
    
    return landing_page_threads

if __name__ == "__main__":
    oen_default_url = "https://www.threads.com/search?q=oen.tw&serp_type=default"
    keyword_oen_recent = "https://www.threads.com/search?q=oen.tw&serp_type=default&filter=recent"
    nat_geo_url = "https://www.threads.net/t/C8H5FiCtESk/"
    threads_dict = scrape_thread(keyword_oen_recent)

    csv_file_name = "first-try-threads.csv"
    # csv_buffer = io.StringIO()
    keys = threads_dict[0].keys() if threads_dict else []
    with open(csv_file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(threads_dict)
    
    print(f"Saved {len(threads_dict)} threads to {csv_file_name}")