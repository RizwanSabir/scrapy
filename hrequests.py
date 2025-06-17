import hrequests
import random

import requests
import gzip
from io import BytesIO
import xml.etree.ElementTree as ET

status_200=0
status_403=0
def load_proxies(file_path="proxy.txt"):
    with open(file_path, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies

def create_session(browser="firefox", os=None, version=None):
    if browser == "firefox":
        session = hrequests.firefox.Session(os=os, version=version)
    elif browser == "chrome":
        session = hrequests.chrome.Session(os=os, version=version)
    else:
        session = hrequests.Session(browser, version=version)
    return session

def is_proxy_working(proxy):
    """Simple check to verify if proxy is functional."""
    try:
        session = create_session()
        session.proxy = proxy
        response = session.get("https://httpbin.org/ip", timeout=5)
        session.close()
        return response.status_code == 200
    except Exception:
        return False
global_session = None


def request_with_random_proxy(url, proxies):
    global status_200, status_403, global_session

    os_choices = ['win', 'mac', 'lin']
    browser_choices = ['firefox', 'chrome']

    if global_session:
        try:
            response = global_session.get(url)
            print(f"[REUSING SESSION] => {response.status_code} | {response.url}")

            if response.status_code == 200:
                status_200 += 1
                print(f"Status_200 = {status_200} || Status_403 = {status_403}")
                return response
            elif response.status_code == 403:
                status_403 += 1
                print(f"403 Forbidden. Resetting session.")
                global_session.close()
                global_session = None
                return None

        except Exception as e:
            print(f"[REUSING SESSION FAILED]: {e}")
            global_session.close()
            global_session = None

    random.shuffle(proxies)
    for selected_proxy in proxies:
        if is_proxy_working(selected_proxy):
            selected_os = random.choice(os_choices)
            selected_browser = random.choice(browser_choices)

            session = None
            try:
                session = create_session(browser=selected_browser, os=selected_os)
                session.proxy = selected_proxy

                response = session.get(url)
                print(
                    f"[{selected_os.upper()} | {selected_browser.upper()}] via {selected_proxy} => {response.status_code} | {response.url}")

                if response.status_code == 200:
                    status_200 += 1
                    global_session = session  # ✅ Store for reuse
                    print(f"Status_200 = {status_200} || Status_403 = {status_403}")
                    return response
                elif response.status_code == 403:
                    status_403 += 1
                    print(f"403 Forbidden. Not storing session.")
                    session.close()

            except Exception as e:
                print(f"Request failed with proxy {selected_proxy} ({selected_os} / {selected_browser}): {e}")
                if session:
                    session.close()

    print("No working proxy found.")
    return None


def fetch_and_parse_sitemap(url):
    response = requests.get(url)
    response.raise_for_status()
    content = response.content

    if content[:2] == b'\x1f\x8b':
        with gzip.open(BytesIO(content), 'rb') as f:
            xml_data = f.read()
    else:
        xml_data = content

    root = ET.fromstring(xml_data)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = [url_elem.text for url_elem in root.findall(".//ns:loc", namespaces=namespace)]
    return urls


if __name__ == "__main__":
    proxies = load_proxies("proxy.txt")

    SITEMAP_URL = "https://www.zillow.com/xml/sitemaps/us/hdp/for-rent/sitemap-0002.xml.gz"
    print("Fetching sitemap and parsing URLs...")
    all_urls = fetch_and_parse_sitemap(SITEMAP_URL)

    for i in range(len(all_urls)):  # make 5 different requests
        request_with_random_proxy(all_urls[i], proxies)
