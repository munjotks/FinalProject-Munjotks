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
        price = price.strip('$')
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
	    "ProductPrice"	NUMERIC,
	    "NumStars"	NUMERIC,
	    "NumReviews"	NUMERIC,
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
        if ele == 'highest' or ele == 'lowest' or ele == 'graph':
            return
        yield ele

def process_command(command):
    command = command.lower()    
    digit = any(i.isdigit() for i in command)

    if 'reviews' in command and 'stars' in command and 'price' in command:
        print("Command not recognized: Please input only 2 variation of parameters ")
        raise SystemExit(0)

    if digit == False:
        numresults = 10
    else:
        numresults = re.search(r'\d+', command).group()
    
    connection = sqlite3.connect(DBNAME)
    cursor = connection.cursor()

    # just price
    if 'price' in command and 'review' not in command and 'star' not in command:
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
    elif 'price' in command and 'review' in command and 'star' not in command:
        splitcommand = command.split()
        if splitcommand[1] == 'price':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'highest':
                    #lowest price highest review
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumReviews DESC LIMIT ?", (numresults,))
                else:
                    #lowest price lowest review
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumReviews ASC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'highest':
                    #highest price highest review
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumReviews DESC LIMIT ?", (numresults,))
                else:
                    #highest price lowest review
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumReviews ASC LIMIT ?", (numresults,))
        elif splitcommand[1] == 'review':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'lowest':
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, ProductPrice ASC LIMIT ?", (numresults,))
                else:
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, ProductPrice DESC LIMIT ?", (numresults,))
            else:
                #highest review lowest price
                if splitcommand[2] == 'lowest':
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, ProductPrice ASC LIMIT ?", (numresults,))
                else:
                    #highest review highest price
                    price_review_query = cursor.execute("SELECT ProductName, ProductPrice, NumReviews, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, ProductPrice DESC LIMIT ?", (numresults,))         
    # price and stars
    elif 'price' in command and 'star' in command and 'review' not in command:
        splitcommand = command.split()
        if splitcommand[1] == 'price':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'lowest':
                    #lowest price lowest stars
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumStars ASC LIMIT ?", (numresults,))
                else:
                    #lowest price highest stars
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice ASC, NumStars DESC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'highest':
                    #highest price highest stars
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumStars DESC LIMIT ?", (numresults,))
                else: 
                    #highest price lowest stars
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY ProductPrice DESC, NumStars ASC LIMIT ?", (numresults,))
        elif splitcommand[1] == 'stars':
            if splitcommand[0] == 'lowest':
                if splitcommand[2] == 'lowest':
                    #lowest stars lowest price
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, ProductPrice ASC LIMIT ?", (numresults,))
                else: 
                    #lowest stars highest price
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, ProductPrice DESC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'lowest':
                    #highest stars lowest price
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, ProductPrice ASC LIMIT ?", (numresults,))
                else: 
                    #highest stars highest price
                    price_stars_query = cursor.execute("SELECT ProductName, ProductPrice, NumStars, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, ProductPrice DESC LIMIT ?", (numresults,))
    # reviews and stars
    elif 'review' in command and 'star' in command and 'price' not in command:
        splitcommand = command.split()
        if splitcommand[1] == 'reviews':
            if splitcommand[0] == 'highest':
                if splitcommand[2] == 'highest':
                    #highest reviews highest stars
                    review_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, NumStars DESC LIMIT ?", (numresults,))
                else:
                    #highest reviews lowest stars
                    reviews_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews DESC, NumStars ASC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'lowest':
                    #lowest reviews lowest stars
                    reviews_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, NumStars ASC LIMIT ?", (numresults,))
                else:
                    #lowest reviews highest stars
                    reviews_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumReviews ASC, NumStars DESC LIMIT ?", (numresults,))
        elif splitcommand[1] == 'stars':
            if splitcommand[0] == 'highest':
                if splitcommand[2] == 'highest':
                    #highest stars highest reviews
                    reviews_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, NumReviews DESC LIMIT ?", (numresults,))
                else:
                    #highest stars lowest reviews
                    reviews_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars DESC, NumReviews ASC LIMIT ?", (numresults,))
            else:
                if splitcommand[2] == 'highest':
                    #lowest stars highest reviews
                    reviews_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, NumReviews DESC LIMIT ?", (numresults,))
                else:
                    #lowest stars lowest reviews
                    reviews_stars_query = cursor.execute("SELECT ProductName, NumReviews, NumStars, ProductPrice, SearchTermCategory, ProductURL FROM Products GROUP BY ProductURL ORDER BY NumStars ASC, NumReviews ASC LIMIT ?", (numresults,))
    productdata = cursor.fetchall()
    connection.close()
    return productdata

def printing_results_of_command(productdata, command):
    if 'price' in command and 'review' in command and 'stars' not in command:
        if 'graph' in command:
            names = []
            prices = []
            numreviews = []
            for product in productdata:
                names.append(product[0])
                prices.append(product[1])
                numreviews.append(product[2])
            scatter_data = go.Scatter(
                x=numreviews,
                y=prices,
                text=names,
                marker={'symbol':'circle', 'size':20, 'color':'green'},
                mode='markers+text',
                textposition='top center')
            basic_layout = go.Layout(title="Amazon Product Prices vs Number of Reviews")
            fig = go.Figure(data=scatter_data, layout=basic_layout)
            fig.show()
        else:
            row = " {ProductName:<16s}  {ProductPrice}  {NumReviews}  {SearchTermCategory:<16s}  {ProductURL:<10s}".format
            for product in productdata:
                print(row(ProductName=product[0][:15], ProductPrice=product[1], NumReviews=product[2], SearchTermCategory=product[3][:20], ProductURL=product[4]))
    elif 'price' in command and 'stars' in command and 'reviews' not in command:
        if 'graph' in command:
            names = []
            prices = []
            stars = []
            for product in productdata:
                names.append(product[0])
                prices.append(product[1])
                stars.append(product[2])
            scatter_data = go.Scatter(
                x=prices,
                y=stars,
                text=names,
                marker={'symbol':'circle', 'size':20, 'color':'green'},
                mode='markers+text',
                textposition='top center')
            basic_layout = go.Layout(title="Amazon Product Prices vs Number of Stars(Rating)")
            fig = go.Figure(data=scatter_data, layout=basic_layout)
            fig.show()
        else:
            row = "{ProductName:<16s}  {ProductPrice}  {NumStars}  {SearchTermCategory:<16s}  {ProductURL:<10s}".format
            for product in productdata:
                print(row(ProductName=product[0][:15], ProductPrice=product[1], NumStars=product[2], SearchTermCategory=product[3][:20], ProductURL=product[4]))
    elif 'stars' in command and 'reviews' in command and 'price' not in command:
        if 'graph' in command:
            names = []
            stars = []
            numreviews = []
            for product in productdata:
                names.append(product[0])
                stars.append(product[2])
                numreviews.append(product[1])
            scatter_data = go.scatter(
                x=stars,
                y=numreviews,
                text=names,
                marker={'symbol':'circle', 'size':20, 'color':'green'},
                mode='markers+text',
                textposition='top center')
            basic_layout = go.Layout(title="Number of Reviews for Amazon Products vs Amazon Product Rating")
            fig = go.Figure(data=scatter_data, layout=basic_layout)
            fig.show()
        else:
            row = " {ProductName:<16s}  {NumReviews}  {NumStars} {ProductPrice} {SearchTermCategory:<16s}  {ProductURL:<10s}".format
            for product in productdata:
                print(row(ProductName=product[0][:15], NumReviews=product[1], NumStars=product[2], ProductPrice=product[3], SearchTermCategory=product[4][:20], ProductURL=product[5]))
    elif 'price' in command and 'stars' not in command and 'reviews' not in command:
        if 'graph' in command:
            xaxis = []
            yaxis = []
            for product in productdata:
                xaxis.append(product[0])
                yaxis.append(product[1])
            barsbarplot = go.Bar(x=xaxis, y=yaxis)
            basic_layout = go.Layout(title="Amazon Product Prices")
            fig = go.Figure(data=barsbarplot, layout=basic_layout)
            fig.show()
        else:
            row = " {ProductName:<16s} {ProductPrice} {SearchTermCategory:<16s}  {ProductURL:<10s}".format
            for product in productdata:
                print(row(ProductName=product[0][:15], ProductPrice=product[1], SearchTermCategory=product[2][:20], ProductURL=product[3]))
    elif 'stars' in command and 'price' not in command and 'reviews' not in command:
        if 'graph' in command:
            xaxis = []
            yaxis = []
            for product in productdata:
                xaxis.append(product[0])
                yaxis.append(product[1])
            barsbarplot = go.Bar(x=xaxis, y=yaxis)
            basic_layout = go.Layout(title="Amazon Product Stars out of 5")
            fig = go.Figure(data=barsbarplot, layout=basic_layout)
            fig.show()
        else:
            row = " {ProductName:<16s} {NumStars} {SearchTermCategory:<16s}  {ProductURL:<10s}".format
            for product in productdata:
                print(row(ProductName=product[0][:15], NumStars=product[1], SearchTermCategory=product[2][:20], ProductURL=product[3]))
    elif 'reviews' in command and 'stars' not in command and 'price' not in command:
        if 'graph' in command:
            xaxis = []
            yaxis = []
            for product in productdata:
                xaxis.append(product[0])
                yaxis.append(product[1])
            barsbarplot = go.Bar(x=xaxis, y=yaxis)
            basic_layout = go.Layout(title="Amazon Products by Number of Reviews")
            fig = go.Figure(data=barsbarplot, layout=basic_layout)
            fig.show()
        else:
            row = " {ProductName:<16s} {NumReviews} {SearchTermCategory:<16s}  {ProductURL:<10s}".format
            for product in productdata:
                print(row(ProductName=product[0][:15], NumReviews=product[1], SearchTermCategory=product[2][:20], ProductURL=product[3]))

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

        if response == 'graph':
            response = 'lowest price 10 graph'
        
        # # Create a string of words from list for create_url Function [searchterm]
        searchterm = " ".join(searchwords)
        searchpageurl = create_url(searchterm)
        
        # # crawl and scrape amazon pages to extract lists of products when a specific query is searched
        productlists = get_product_instance(searchpageurl, searchterm)
        create_csv(productlists)

        # # # Create a database to pull information from
        create_db()
        load_products()

        #extract data from database by user command
        datafromsqlite = process_command(response)
        # print(datafromsqlite[0])

        # displaying results from user command
        displayresults = printing_results_of_command(datafromsqlite, response)

    return displayresults

if __name__ == "__main__":
    interactive_prompt()


    

