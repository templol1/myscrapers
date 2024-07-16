import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape(base_url, use_pointer, tag_identifier):
    pointer = 0
    hrefs = []

    while True:
        url = f"{base_url}/{pointer}" if use_pointer and pointer != 0 else base_url

        response = requests.get(url)
        if response.status_code != 200:
            break

        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')

        if use_pointer:
            anchors = soup.find_all('a', {'data-testid': tag_identifier})
            hrefs.extend([anchor.get('href') for anchor in anchors if anchor.get('href')])
        else:
            class_name = tag_identifier
            links = soup.find_all('a', class_=class_name)
            hrefs.extend([link['href'] for link in links if link.get('href')])
            break
         
        pointer += 1

    return hrefs

def download_file(url, dest):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    t = tqdm(total=total_size, unit='iB', unit_scale=True, desc=dest, leave=False)

    with open(dest, 'wb') as file:
        for data in response.iter_content(block_size):
            t.update(len(data))
            file.write(data)
    t.close()

base_url = input("Enter the url:")
print("Please wait, we are seeing how many videos there are... (the more videos, the more longer)")
hrefs = scrape(base_url, True, 'video-thumb-title')
vids = []
prog = 1
total = len(hrefs)
for item in hrefs:
    print(f"Progress: {prog}/{total}")
    vids.extend(scrape(item, False, 'player-container__no-player xplayer xplayer-fallback-image xh-helper-hidden'))
    prog += 1

max_workers = 4
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_url = {executor.submit(download_file, vid, f"video_{i}.mp4"): vid for i, vid in enumerate(vids)}

    for future in tqdm(as_completed(future_to_url), total=len(future_to_url), desc="Downloading videos"):
        try:
            future.result()
        except Exception as exc:
            print(f"An error occurred: {exc}")

print("All downloads completed.")
