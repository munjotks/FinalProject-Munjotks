#################################
##### Name: Munjot Singh
##### Uniqname: Munjotks
#################################

from bs4 import BeautifulSoup
import requests
import json
import csv
import sqlite3
import plotly.graph_objects as go
import re

headers = {
    'User-Agent': 'UMSI 507 Course Final Project - Python Scraping',
    'From': 'Munjotks@umich.edu',
    'Course-Info': 'https://si.umich.edu/programs/courses/507' 
}

CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

DBNAME = 'AmazonProductInfo.sqlite'

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

class AmazonProduct:
    '''
    docstring
    '''

    def __init__(self, category, productname, productprice, numstars, numreviews, url):
        self.category = category
        self.productname = productname
        self.productprice = productprice
        self.numstars = numstars
        self.numreviews = numreviews
        self.url = url
    
    def info(self):
        return f"{self.category}: {self.productname}, {self.productprice}, {self.numstars}, {self.numreviews}, {self.url}"

def create_url(searchterm):
    if ' ' in searchterm:
        searchterm = searchterm.replace(' ', '+')
    base_url = 'https://www.amazon.com/s?k={}&ref=nb_sb_noss_1'
    url = base_url.format(searchterm)
    return url


def get_next_page_url(soup):
    # next_page = soup.find(class_='a-normal').find('a')['href']
    find_links = soup.find_all(class_='celwidget slot=MAIN template=PAGINATION widgetId=pagination-button')
    for link in find_links:
        next_page_text = link.find_all(class_='a-last')
        for text in next_page_text:
            urltext = text.find('a')
            next_page = urltext['href']
    
    if (next_page is not None):
        base_url = 'https://www.amazon.com'
        next_page_url = base_url + next_page
        return next_page_url
    else:
        return None

# url_text = make_url_request_using_cache('https://www.amazon.com/s?k=amazon&page=3&qid=1608079364&ref=sr_pg_3', CACHE_DICT)
# soup = BeautifulSoup(url_text, 'html.parser')
# next_page = soup.find_all(class_='celwidget slot=MAIN template=PAGINATION widgetId=pagination-button')
# for link in next_page:
#     url = link.find_all(class_='a-last')
#     for a in url:
#         urllink = a.find('a')
#         urlhref = urllink['href']
#         print(urlhref)

def get_product_instance(search_product_url, searchterm):
    '''
    Docstring
    '''
    url_text = make_url_request_using_cache(search_product_url, CACHE_DICT)
    soup = BeautifulSoup(url_text, 'html.parser')

    next_page_url = get_next_page_url(soup=soup)

    products = []
    while (next_page_url is not None):
        searchresultspage = soup.find_all('div', {'data-component-type': 's-search-result'})
        for item in searchresultspage:
            product = parse_each_product(item=item, searchterm=searchterm)
            if product:
                products.append(product)

        if next_page_url == False:
            next_page_url = None
        else:
            url_text = make_url_request_using_cache(next_page_url, CACHE_DICT)
            soup = BeautifulSoup(url_text, 'html.parser')
            pageresults = soup.find_all('div', {'data-component-type': 's-search-result'})
            for item in pageresults:
                product = parse_each_product(item=item, searchterm=searchterm)
                if product:
                    products.append(product)

            try:
                next_page_url = get_next_page_url(soup=soup)
            except:
                next_page_url = False

    return products

# print(get_product_instance('https://www.amazon.com/s?k=camera&ref=nb_sb_noss_2', 'camera'))

def parse_each_product(item, searchterm):
    '''
    Docstring
    '''
    atag = item.h2.a 

    # Get product names
    description = atag.text.strip()

    # Get product URL
    url = 'https://www.amazon.com' + atag.get('href')

    # Get product price
    try:
        price1 = item.find('span', 'a-price')
        price = price1.find('span', 'a-offscreen').text
    except AttributeError:
        return
    
    # Get # of Stars
    try:
        numstars = item.i.text
        numstars = numstars.split(' ')
        numstars = numstars[0]
    except AttributeError:
        numstars = ''
    
    # Get # of Reviews
    try:
        numreviews = item.find('span', {'class': 'a-size-base', 'dir': 'auto'}).text
    except AttributeError:
        numreviews = ''

    productinfo = (searchterm, description, price, numstars, numreviews, url)
    return productinfo

def create_csv(productinformation):
    with open('results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['SearchTermCategory', 'ProductName', 'ProductPrice', 'NumStars', 'NumReviews', 'URL'])
        writer.writerows(productinformation)

def create_db():
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    drop_products_sql = 'DROP TABLE IF EXISTS "Products"'

    create_products_sql = '''
        CREATE TABLE IF NOT EXISTS "Products" (
        "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
	    "SearchTermCategory"	TEXT NOT NULL,
	    "ProductName"	TEXT NOT NULL,
	    "ProductPrice"	INTEGER,
	    "NumStars"	INTEGER,
	    "NumReviews"	INTEGER,
	    "ProductURL"	TEXT    
        )
    '''

    cur.execute(drop_products_sql)
    cur.execute(create_products_sql)
    conn.commit()
    conn.close()

def load_products():
    file_contents = open('results.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)

    insert_product_sql = '''
        INSERT INTO Products
        VALUES (NULL, ?, ?, ?, ?, ?, ?)
    '''

    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    for row in csv_reader:

        cur.execute(insert_product_sql, [
            row[0], #SearchTermCategory
            row[1], #ProductName
            row[2], #ProductPrice
            row[3], #NumStars
            row[4], #NumReview
            row[5] #URL
        ])

    conn.commit()
    conn.close()

def load_help_text():
    with open('AmazonHelp.txt') as f:
        return f.read()

def print_ele(response):
    for ele in response:
        if ele == 'highest' or ele == 'lowest':
            return
        yield ele

def process_command(command):
    command = command.lower()    
    digit = any(i.isdigit() for i in command)

    if digit == False:
        numresults = 10
    else:
        numresults = re.search(r'\d+', command).group()
    
    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()

    # just price
    if 'price' in command and 'reviews' not in command and 'stars' not in command:
        if 'highest' in command:
            price_query = cursor.execute("SELECT ProductName, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC LIMIT ?", (numresults,))
        else:
            price_query = cursor.execute("SELECT ProductName, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC LIMIT ?", (numresults,))
    # just reviews
    elif 'reviews' in command and 'price' not in command and 'stars' not in command:
        if 'highest' in command:
            review_query = cursor.execute("SELECT ProductName, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC LIMIT ?", (numresults,))
        else:
            review_query = cursor.execute("SELECT ProductName, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC LIMIT ?", (numresults,))
    # just stars
    elif 'stars' in command and 'price' not in command and 'reviews' not in command:
        if 'highest' in command:
            stars_query = cursor.execute("SELECT ProductName, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC LIMIT ?", (numresults,))
        else:
            stars_query = cursor.execute("SELECT ProductName, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC LIMIT ?", (numresults,))
    # price and reviews
    elif 'price' in command and 'reviews' in command and 'stars' not in command:
        splitcommand = command.split()
        if splitcommand[1] == 'price':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'highest':
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumReviews DESC LIMIT ?", (numresults,))
                else:
                    price_review_query = ("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumReviews ASC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'highest':
                    price_review_query = ("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumReviews DESC LIMIT ?", (numresults,))
                else: 
                    price_review_query = ("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumReviews ASC LIMIT ?", (numresults,))
        elif splitcommand[1] == 'review':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'lowest':
                    price_review_query = ("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, ProductPrice ASC LIMIT ?", (numresults,))
                else:
                    price_review_query = ("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, ProductPrice DESC LIMIT ?", (numresults,))
            else:
                #highest review lowest price
                if splitcommand[2] == 'lowest':
                    price_review_query = ("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, ProductPrice ASC LIMIT ?", (numresults,))
                else:
                    #highest review highest price
                    price_review_query = ("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, ProductPrice DESC LIMIT ?", (numresults,))         
    # price and stars
    elif 'price' in command and 'stars' in command and 'reviews' not in command:
        if splitcommand[1] == 'price':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'lowest':
                    #lowest price lowest stars
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumStars ASC LIMIT ?", (numresults,))
                else:
                    #lowest price highest stars
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumStars DESC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'highest':
                    #highest price highest stars
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumStars DESC LIMIT ?", (numresults,))
                else: 
                    #highest price lowest stars
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumStars ASC LIMIT ?", (numresults,))
        elif splitcommand[1] == 'stars':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'lowest':
                    #lowest stars lowest price
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, ProductPrice ASC LIMIT ?", (numresults,))
                else: 
                    #lowest stars highest price
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, ProductPrice DESC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'lowest':
                    #highest stars lowest price
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, ProductPrice ASC LIMIT ?", (numresults,))
                else: 
                    #highest stars highest price
                    price_stars_query = ("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, ProductPrice DESC LIMIT ?", (numresults,))
    # reviews and stars
    elif 'reviews' in command and 'stars' in command and 'price' not in command:
        if splitcommand[1] == 'reviews':
            if splitcommand[0] == 'highest':
                if splitcommand[2] == 'highest':
                    #highest reviews highest stars
                    review_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, NumStars DESC LIMIT ?", (numresults,))
                else:
                    #highest reviews lowest stars
                    reviews_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, NumStars ASC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'lowest':
                    #lowest reviews lowest stars
                    reviews_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, NumStars ASC LIMIT ?", (numresults,))
                else:
                    #lowest reviews highest stars
                    reviews_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, NumStars DESC LIMIT ?", (numresults,))
        elif splitcommand[1] == 'stars':
            if splitcommand[0] == 'highest':
                if splitcommand[2] == 'highest':
                    #highest stars highest reviews
                    reviews_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, NumReviews DESC LIMIT ?", (numresults,))
                else:
                    #highest stars lowest reviews
                    reviews_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, NumReviews ASC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'highest':
                    #lowest stars highest reviews
                    reviews_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, NumReviews DESC LIMIT ?", (numresults,))
                else:
                    #lowest stars lowest reviews
                    reviews_stars_query = ("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, NumReviews ASC LIMIT ?", (numresults,))
    productdata = cursor.fetchall()
    connection.close()
    return productdata

def interactive_prompt():
    help_text = load_help_text()
    response = ''
    while response != 'exit':
        response = input("What item would you like to search on Amazon? ")
        if response == 'help':
            print(help_text)
            continue
        response = response.lower().split(' ')
        searchwords = list(print_ele(response))
        # Create Command to lookup data in database [response]
        for x in searchwords:
            if x in response:
                response.remove(x)
        if not response:
            response = 'lowest price 10'
        else:
            response = " ".join(response)
        
        # Create a string of words from list for create_url Function [searchterm]
        searchterm = " ".join(searchwords)
        searchpageurl = create_url(searchterm)
        
        # crawl and scrape amazon pages to extract lists of products when a specific query is searched
        productlists = get_product_instance(searchpageurl, searchterm)
        create_csv(productlists)

        # # Create a database to pull information from
        create_db()
        load_products()

        



if __name__ == "__main__":
    interactive_prompt()


    

