import requests,re,os,shutil,zipfile,subprocess
from tqdm import tqdm
import mimetypes
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
# requests bs4 tqdm selenium
def scrape(base_url, use_pointer):
    pointer = 1
    hrefs = []

    while True:
        url = f"{base_url}{pointer}/" if use_pointer and pointer != 1 else base_url

        response = requests.get(url)
        if response.status_code != 200:
            break

        html = response.content
        soup = BeautifulSoup(html, 'html.parser')

        if use_pointer:
            div_list_videos = soup.find('div', class_='list-videos')
            if div_list_videos:
                a_tags = div_list_videos.find_all('a')
                for a in a_tags:
                    href = a.get('href')
                    title = a.get('title')
                    if href and title:
                        hrefs.append({'href': href, 'title': title})  
                    
            pointer += 1
         
    return hrefs


def getVid(links):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--log-level=3')
    webdriver_service = Service(os.path.abspath('driver/chromedriver-win64/chromedriver.exe'))
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
    for pointer, link in enumerate(links, start=1):
        print(f'Progress: {pointer}/{len(links)}')
        toScrape = link['href']  
        try:
            driver.get(toScrape)
            video_element = driver.find_element(By.CSS_SELECTOR, "div.fp-player > video")
            video_src = video_element.get_attribute("src")
            link['href'] = video_src
        except:
            print("Private video... skip")
            link['href'] = "na"
        pointer += 1
    return links



def Downloader(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            file.write(response.content)
        print('File downloaded successfully.')
    else:
        print('Failed to retrieve the file. Status code:', response.status_code)

def getDrivers():
    if os.path.exists('driver'):
        shutil.rmtree('driver')
    os.makedirs(f'driver')
    print("Getting the latest version of chrome...")
    Downloader('https://ninite.com/chrome/ninite.exe', 'driver/Ninite.exe')
    Downloader('https://github.com/cramaboule/Silent-Ninite/archive/refs/heads/main.zip', 'driver/silent.zip')
    with zipfile.ZipFile('driver/silent.zip', 'r') as zip_ref:
        zip_ref.extractall('driver/')
    shutil.copy('driver/Ninite.exe', 'driver/Silent-Ninite-main/Ninite.exe')
    exe_path = os.path.abspath('driver/Silent-Ninite-main/ninite-silent.exe')
    result = subprocess.run(exe_path, check=True)
    print(result)
    print("Getting webdriver...")
    url = "https://googlechromelabs.github.io/chrome-for-testing/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    stable_section = soup.find('section', {'id': 'stable'})
    version_info = stable_section.find('p').text
    latest_version = version_info.split()[1]  
    Downloader(f'https://storage.googleapis.com/chrome-for-testing-public/{latest_version}/win64/chromedriver-win64.zip', 'driver/driver.zip')
    with zipfile.ZipFile('driver/driver.zip', 'r') as zip_ref:
        zip_ref.extractall('driver/')

def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def get_file_extension(href, response):
    if '.' in href.split('/')[-1]:
        return href.split('.')[-1]
    else:
        content_type = response.headers.get('content-type')
        if content_type:
            return mimetypes.guess_extension(content_type.split(';')[0])
    return ''

def download_file(session, href, title, folder_path):
    if href != "na":
        response = session.get(href, stream=True)
        file_extension = get_file_extension(href, response)
        file_name = f"{title}{file_extension}"
        file_path = os.path.join(folder_path, file_name)
        
        total_size = int(response.headers.get('content-length', 0))
        with open(file_path, 'wb') as file, tqdm(
            desc=title,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                file.write(data)
                bar.update(len(data))

def download_files(hrefs, folder_path):
    create_folder_if_not_exists(folder_path)
    with ThreadPoolExecutor(max_workers=4) as executor:
        with requests.Session() as session:
            futures = [
                executor.submit(download_file, session, item['href'], item['title'], folder_path)
                for item in hrefs
            ]
            for future in futures:
                future.result()


print("This only works for Windows systems...")
print("You do not need to do anything beforehand, we have it under control! Please make sure a folder named ""driver"" does not exist!")
username = input("Username as seen in URL:")
getDrivers()
vidUrls = scrape(f'https://www.shemale6.com/models/{username}/', True)
downloadLinks = getVid(vidUrls)
download_files(downloadLinks, username)
shutil.rmtree('driver')




