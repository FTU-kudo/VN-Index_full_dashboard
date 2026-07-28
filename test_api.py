import requests, re
html = requests.get('https://ysradar.yuanta.com.vn').text
js_files = re.findall(r'src="(.*?\.js)"', html)
for js in set(js_files):
    if not js.startswith('http'): js = 'https://ysradar.yuanta.com.vn' + ('' if js.startswith('/') else '/') + js
    try:
        content = requests.get(js).text
        if 'correlate' in content:
            print(f'Found in {js}')
            idx = content.find('correlate')
            print(content[max(0, idx-100):idx+200])
    except: pass
