from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from urllib.parse import quote,unquote,urljoin
import html
import re
import requests
import sys
import os
import time
import json
import html2text
import pandas as pd
import shutil
import csv
import argparse
import traceback

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
 
os.chdir(application_path)

facebook_session_profile = os.path.join(application_path,"facebook_profile")

headers_html = {
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36 Edg/104.0.1293.54",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    'referer':'https://www.google.com/'
}

def initialize_chrome():
    global driver 
    try:
        print("Initializing chromedriver.")
        options = Options()
        options.add_argument(f'--user-data-dir={facebook_session_profile}')
        options.add_argument("--start-maximized")
        options.add_argument("--disable-gpu")
        options.add_argument('--log-level=3')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        time.sleep(3)
        return True
    except Exception as e:
        print(e)
        pass

     
  
def profile_photo(url,profile_name,profile="",cover=""):
    profile_pic = None
    coverphoto = None
    print(profile)
    s = requests.Session()      
    driver.get(url)
    time.sleep(2)
    source_text_main = driver.page_source
    
    if "<title>Facebook</title>" in source_text_main:
        print("Restricted or Invalid : ",url)
        return
      
    if not os.path.exists(profile):
        try:    
            profile_pic = re.search("\"profile_photo\":{\"url\":\"(.*?)\",.+?}",source_text_main).groups()[0]
            profile_pic = profile_pic.replace('\\/','/')
            
            driver.get(profile_pic)
            source_text = driver.page_source
            profile_pic = re.search("\"image\":{\"uri\":\"(.*?)\",.+?}",source_text).groups()[0]
            profile_pic = profile_pic.replace('\\/','/')
           
            r = requests.get(profile_pic,headers=headers_html)
            if r.status_code==200:
                if 'image' in r.headers.get('content-type',''):
                    with open(profile,'wb') as f:
                        f.write(r.content)
                    print('Profile Downloaded : ',profile)                    
        except:
            try:          
                soup = BeautifulSoup(source_text_main,'lxml')
                picture_div = soup.find('div',{'class':'b3onmgus e5nlhep0 ph5uu5jm ecm0bbzt spb7xbtv bkmhp75w emlxlaya s45kfl79 cwj9ozl2'})
                profile_pic= picture_div.find('image').get('xlink:href')
                r = requests.get(profile_pic,headers=headers_html)
                if r.status_code==200:
                    if 'image' in r.headers.get('content-type',''):
                        with open(profile,'wb') as f:
                            f.write(r.content) 
                        print('Profile Downloaded : ',profile)     
            except:
                pass
    
    if not os.path.exists(cover):
        try:
            coverphoto = re.search(r"<a aria-label\=\"Link to open (?:page|profile) cover photo\"[\s\S\n]+?href=\"(.+?)\"",source_text_main).groups()[0]
            coverphoto = coverphoto.replace('\\/','/')
            
            driver.get(coverphoto)
            source_text = driver.page_source
            coverphoto = re.search("\"image\":{\"uri\":\"(.*?)\",.+?}",source_text).groups()[0]
            coverphoto = coverphoto.replace('\\/','/')
            r = requests.get(coverphoto,headers=headers_html)
            if r.status_code==200:
                if 'image' in r.headers.get('content-type',''):
                    with open(cover,'wb') as f:
                        f.write(r.content)            
                    print('Cover Downloaded : ',cover)
        except:
            try:
                soup = BeautifulSoup(source_text_main,'lxml')
                cover_img = soup.find('img',{'data-imgperflogname':'profileCoverPhoto'})
                coverphoto = urljoin("https://www.facebook.com/",cover_img['src'])
                r = requests.get(coverphoto,headers=headers_html)
                if r.status_code==200:
                    if 'image' in r.headers.get('content-type',''):
                        with open(cover,'wb') as f:
                            f.write(r.content) 
                        print('Cover Downloaded : ',cover)
            except:
                pass
    
    if not (os.path.exists(cover) or os.path.exists(profile)):
        shutil.rmtree(os.path.dirname(profile))      



def main():
    tutorial = ''
    arg_parser = argparse.ArgumentParser(description='Download High Quality Facebook Profile and Cover Photos.')
    
    arg_parser.add_argument('-f','--file-path',
        metavar=' ',
        type=str,
        help='CSV or Excel Filepath',
        required=True)
    
    arg_parser.add_argument('-t','--file-type',
        metavar=' ',
        type=str,
        help="File type \"excel\" or \"csv\".",
        required=True)
    
    arg_parser.add_argument('-l','--login',help="Use Login.",action='store_true')
    
    args = arg_parser.parse_args()
   
    filepath = args.file_path
    filetype = args.file_type.lower().strip()
    if filetype=='excel':    
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)
        
    records = df.to_dict('records')
    
    data = {}
    
    for record in records:
        fb_name,fb_link = record['Name'], record['Link']
        fb_name = re.sub('[\\/:*?"<>|]', '', fb_name)  # remove all windows illegal characters
        if data.get(fb_name):
            c = 1
            while True:
                if not data.get(fb_name+" {c}"):
                    data[fb_name+" {c}"] = fb_link
                    break
                c+=1
        else:
            data[fb_name] = fb_link

    if not initialize_chrome():
        print("Error : ", "Failed to start chromedriver")
        sys.exit(1)
    if args.login:
        input('Press enter after you\'ve logged in.')
        
    for fb_name,fb_link in data.items():
        dirname = os.path.join("Images",fb_name)
        
        if not os.path.exists(dirname):
            os.makedirs(dirname)
                   
        profilepath = os.path.abspath(os.path.join(dirname,"profile.jpg"))
        
        coverpath = os.path.abspath(os.path.join(dirname,f"cover.jpg"))
        
        if os.path.exists(profilepath) and os.path.exists(coverpath):        
            continue
            
        print("\n","Downloading Profile : ",fb_link)
        profile_photo(fb_link,fb_name,profile=profilepath,cover=coverpath)
       
           
    driver.quit()
        
    
    

if __name__=="__main__":
    main()