#################################
##### Name: Munjot Singh
##### Uniqname: Munjotks
#################################


from bs4 import BeautifulSoup
import requests
import json

header = {
    'User-Agent': 'UMSI 507 Course Final Project - Python Scraping',
    'From': 'Munjotks@umich.edu',
    'Course-Info': 'https://si.umich.edu/programs/courses/507' 
}

def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    if (url in cache.keys()):
        print("Using Cache")
        return cache[url]
    else:
        print("Fetching")
        response = requests.get(url, headers=headers)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

CACHE_DICT = load_cache()

