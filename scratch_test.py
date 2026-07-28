import requests
import re

url = "https://ysradar.yuanta.com.vn/ysradar/stock/VIC/tin-tuc-su-kien"
headers = {
    'User-Agent': 'Mozilla/5.0'
}
res = requests.get(url, headers=headers)
html = res.text

# find all api urls
apis = re.findall(r'https://ysradarapi\.yuanta\.com\.vn/[^"\']+', html)
for api in set(apis):
    print(api)
