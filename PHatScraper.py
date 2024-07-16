# bs4 requests tqdm 
from bs4 import BeautifulSoup
import requests
import os
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import subprocess
print("YOU MUST HAVE FFMPEG INSTALLED AT THE ENV LEVEL")
scrapeUrl = input("Enter Url with the / at the end:")
def scrape(base_url, use_pointer):
    pointer = 1
    hrefs = []

    while True:
        url = f"{base_url}{pointer}/" if use_pointer and pointer != 1 else base_url

        response = requests.get(url)
        if response.status_code != 200:
            break

        html = response.content
        soup = BeautifulSoup(html,'html.parser')

        if use_pointer:
            video_links = soup.find_all('a', href=lambda href: href and href.startswith('/video'))

            video_info = [[a['href'], a.get('title', '')] for a in video_links]

            hrefs.extend(video_info)
         
        pointer += 1
         
    return hrefs

links = scrape(scrapeUrl, True)
def getVid(links):
    pointer = 1
    for link in links:
        print(f'Progress: {pointer}/{len(links)}')
        toScrape = "https://www.pornhat.com" + link[0]
        response = requests.get(toScrape)
        content = response.content
        soup = BeautifulSoup(content, 'html.parser')
        auto_source = soup.find('source', {'title': 'Auto'})
        link[0] = auto_source['src'] if auto_source else None
        pointer = pointer + 1
    
    return links
links = getVid(links)
def download_file(url, name, folder):
    response = requests.get(url, stream=True)
    file_path = os.path.join(folder, f"{name}.mp4")
    
    with open(file_path, 'wb') as f:
        total_size = int(response.headers.get('content-length', 0))
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=name) as pbar:
            for data in response.iter_content(chunk_size=4096):
                f.write(data)
                pbar.update(len(data))

def download(mylist, folder):
    os.makedirs(folder, exist_ok=True)  
    with ThreadPoolExecutor(max_workers=4) as executor:
        for url, name in mylist:
           executor.submit(download_file, url, name, folder)
print(links)
input_folder = "stream"
download(links,input_folder)
output_folder = scrapeUrl.rstrip('/').split('/')[-1]
os.makedirs(output_folder, exist_ok=True)
for filename in os.listdir(input_folder):
   
    if filename.endswith('.mp4'):
        
        old_file = os.path.join(input_folder, filename)
       
        new_file = os.path.join(input_folder, filename.replace('.mp4', '.m3u8'))
       
        os.rename(old_file, new_file)
        print(f'Renamed: {old_file} to {new_file}')

for filename in os.listdir(input_folder):
      
        input_file = os.path.join(input_folder, filename)
        filename_without_extension, _ = os.path.splitext(filename)
     
        output_file = os.path.join(output_folder, filename_without_extension)

        
        command = [
    'ffmpeg',
    '-protocol_whitelist', 'file,crypto,data,http,https,tcp,tls',  
    '-i', input_file, 
    '-c', 'copy',
    '-bsf:a', 'aac_adtstoasc',      
    output_file + ".mp4"       
]


        try:
            subprocess.run(command, check=True)
            print(f'Converted: {input_file} to {output_file}')
        except subprocess.CalledProcessError as e:
            print(f'Error converting {input_file}: {e}')

os.remove(input_folder)
