import requests
import json
import time
import datetime
import os
import psycopg2

#set time variable
times_ran = 0

### Vons ###
url = 'https://shop.vons.com/bin/safeway/login'
base = 'https://shop.vons.com/bin/safeway/product/results'


### Scrape terms ###
ZIP = 92092
KEY = 'promo'
VALUE = 'popular-items-1750'

# data = {'resourcePath': '/content/shop/vons/en/welcome/jcr:content/root/responsivegrid/column_control/par_0/two_column_zip_code_', 'zipcode': 92092}
data = {'zipcode':ZIP}
payload = {'key':KEY, 'value':VALUE}


### Session start ###
s = requests.Session()

s.post(url, data=data)
r = s.get(base, params=payload)

results = r.json()['products']


### Index by id ###
data = {}
for item in results:
    data[item.pop('id')] = item

#set up database
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

#create new table
cur = conn.cursor()

#get column names
items = list(data.values())[0].keys()
columns = list(items)

#create strings for cur.execute
table_columns = [i + " TEXT" for i in columns]
table = "CREATE TABLE popular(ID TEXT,{0})".format(",".join(table_columns))
query = "INSERT INTO popular(ID,{0}) VALUES (%s{1})"
query = query.format(",".join(columns), ",%s" * len(columns))
print(table)

#write to postgres
cur.execute(table)
for ID, rest in data.items():
	keys = (ID,) + tuple(rest[c] for c in columns)
	cur.execute(query, keys)

#delete columns
to_keep = ["price", "name", "sellByWeight", "unitOfMeasure", "aisleName", "shelfName", "pricePer"]
for name in columns:
	if name not in to_keep:
		to_delete = "ALTER TABLE popular DROP COLUMN {0}".format(name)
		cur.execute(to_delete)

#close database
conn.commit()
cur.close()
conn.close()
print("worked")

