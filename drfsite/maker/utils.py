import requests
from bs4 import BeautifulSoup

def fetch_link_data(url):
    data = {
        'title': '',
        'description': '',
        'url': url,
        'image': '',
        'link_type': 'website',
    }
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        og_title = soup.find('meta', property='og:title')
        og_description = soup.find('meta', property='og:description')
        og_image = soup.find('meta', property='og:image')

        data['title'] = og_title['content'] if og_title else soup.title.string if soup.title else ''
        data['description'] = og_description['content'] if og_description else ''
        data['image'] = og_image['content'] if og_image else ''
    except Exception as e:
        print(f"Ошибка при извлечении Open Graph данных: {e}")
    
    return data
