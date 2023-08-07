import time
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pytube import YouTube
import json

from selenium.common.exceptions import TimeoutException


def wait_for_ad_to_finish(driver):
    try:
        # Wait for the skip ad button to be clickable for up to 10 seconds
        skip_ad_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-ad-skip-button")))
        # Click the skip ad button to skip the ad
        skip_ad_button.click()
    except TimeoutException:
        # If the ad skip button is not found or not clickable, just continue without skipping
        pass

def get_video_duration(video_url):
    try:
        yt = YouTube(video_url)
        duration_in_seconds = yt.length
        return duration_in_seconds
    except Exception as e:
        print("Error fetching video duration:", e)
        return None


def watch_video(driver, video_url):
    try:
        driver.get(video_url)
        wait_for_ad_to_finish(driver)  # Wait for the ad to finish before watching the video

        duration = get_video_duration(video_url)
        if duration:
            # Watch 60% of the video
            # time_to_watch = duration * 0.6
            time_to_watch = 10
            time.sleep(time_to_watch)

            # Pause the video after watching
            pause_button = driver.find_element(By.CSS_SELECTOR, '.ytp-play-button')
            pause_button.click()

    except Exception as e:
        print("Error watching video:", e)


def extract_top_related_video_urls(driver):
    related_video_urls = []

    # Find the element containing the related videos section
    related_videos_section = driver.find_element(By.XPATH, '//*[@id="secondary"]')

    # Find all elements containing the related videos' thumbnails
    thumbnail_elements = related_videos_section.find_elements(By.CSS_SELECTOR, 'ytd-thumbnail')

    # Skip the first video recommendation (usually the currently playing video)
    thumbnail_elements = thumbnail_elements[1:]

    # Extract the video URLs from the related videos
    for thumbnail_element in thumbnail_elements:
        try:
            video_url_element = thumbnail_element.find_element(By.CSS_SELECTOR, 'a#thumbnail')
            video_url = video_url_element.get_attribute('href')
            related_video_urls.append(video_url)

            # Stop getting related video URLs once we have 2
            if len(related_video_urls) == 2:
                break
        except Exception as e:
            print("Error extracting related video URL:", e)

    print(related_video_urls)
    return related_video_urls


def process_related_videos(driver, video_url, current_depth, max_depth, skip_first_recommendation=False):
    # Stop if we reached the maximum depth
    if current_depth > max_depth:
        return

    watch_video(driver, video_url)

    # Extract top related videos of the current video
    top_related_videos = extract_top_related_video_urls(driver)

    # Save the top related videos into the JSON file
    with open('related_videos.json', 'a') as json_file:
        json.dump(top_related_videos, json_file)
        json_file.write('\n')

    # Process the top related videos as children (with increased depth)
    for i, related_video in enumerate(top_related_videos):
        # Determine whether to skip the first recommendation based on the flag and video depth
        skip_first = skip_first_recommendation and current_depth == 1 and i == 0
        process_related_videos(driver, related_video, current_depth + 1, max_depth, skip_first_recommendation=skip_first)

def main():
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--mute-audio")  # Mute the entire browser

    with Chrome(options=options) as driver:
        driver.get("https://www.youtube.com")

        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@aria-label="Sign in"]')))
            login_button.click()
            time.sleep(3)

            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="identifierId"]')))
            username_input.send_keys("2023comp480")

            next_button = driver.find_element(By.XPATH, '//*[@id="identifierNext"]/div/button/span')
            next_button.click()
            time.sleep(3)

            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="password"]/div[1]/div/div[1]/input')))
            password_input.send_keys("Comp400research")

            login_button = driver.find_element(By.XPATH, '//*[@id="passwordNext"]/div/button/span')
            login_button.click()
            time.sleep(3)

            # Click on history button using JavaScript
            history_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[text()="History"]')))
            driver.execute_script("arguments[0].click();", history_button)
            time.sleep(3)

            # Click on "Clear all watch history" button using JavaScript
            clear_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[text()="Clear all watch history"]')))
            driver.execute_script("arguments[0].click();", clear_button)

            # Confirm the deletion of watch history
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[text()="Clear watch history"]')))
            driver.execute_script("arguments[0].click();", confirm_button)

        except:
            # If the "Sign in" button is not present, you might already be logged in or there is some other issue
            pass

        # Watch seed videos
        # seed_videos = ['https://www.youtube.com/watch?v=KdoqyKjGpI4&ab_channel=FoxNews',
        #                'https://www.youtube.com/watch?v=N9EsiLE0dyQ&ab_channel=BrianTylerCohen',
        #                'https://www.youtube.com/watch?v=7vnzKPq390Q&feature=youtu.be&ab_channel=TEDxTalks',
        #                'https://www.youtube.com/watch?v=gcQ9sSa5Uhw&feature=youtu.be&ab_channel=ABCNews']
        # Watch seed videos
        seed_videos = ['https://www.youtube.com/watch?v=N9EsiLE0dyQ&ab_channel=BrianTylerCohen']

        for seed_video in seed_videos:
            watch_video(driver, seed_video)

            # Extract related videos from the right sidebar
            related_videos = extract_top_related_video_urls(driver)

            # Save the related videos into a JSON file
            with open('related_videos.json', 'a') as json_file:
                json.dump(related_videos, json_file)
                json_file.write('\n')

            # Process related videos as children with a depth limit of 2
            for related_video in related_videos:
                process_related_videos(driver, related_video, current_depth=1, max_depth=2)

        # Explicitly quit the driver after watching the videos and saving related videos
        driver.quit()


if __name__ == "__main__":
    main()