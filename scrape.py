import requests
from sgselenium import SgChrome
from bs4 import BeautifulSoup as bs
from sgrequests import SgRequests
import re
import pandas as pd
from sgzip.dynamic import DynamicZipSearch, SearchableCountries

locator_domains = []
page_urls = []
location_names = []
street_addresses = []
citys = []
states = []
zips = []
country_codes = []
store_numbers = []
phones = []
location_types = []
latitudes = []
longitudes = []
hours_of_operations = []

s = requests.Session()

search = DynamicZipSearch(country_codes=[SearchableCountries.USA])

# s.get("https://www.rackroomshoes.com/_Incapsula_Resource?SWJIYLWA=5074a744e2e3d891814e9a2dace20bd4,719d34d31c8e3a6e6fffd425f7e032f3")
# print(s.cookies)

base_url = "https://www.rackroomshoes.com"

data_url = "https://www.rackroomshoes.com/store-finder?q=27609&page=1"

url = "https://www.rackroomshoes.com/store-finder"

def parse_response(response, data_url):
    for location in response["data"]:
        locator_domain = "rackroomshoes.com"
        page_url = data_url
        location_name = location["displayName"]
        address = location["line1"]
        city = location["town"]
        state = location["city"]
        zipp = location["postalCode"]
        
        country_code = location["country"]
        if country_code == "United States":
            country_code = "US"

        store_number = location["name"]
        phone = location["phone"]
        location_type = "<MISSING>"
        latitude = location["latitude"]
        longitude = location["longitude"]
        
        hours = ""
        for key in location["openings"].keys():
            hour_bit = location["openings"][key]
            hours = hours + key + " " + hour_bit + ", "
        
        hours = hours[:-2]

        locator_domains.append(locator_domain)
        page_urls.append(page_url)
        location_names.append(location_name)
        street_addresses.append(address)
        citys.append(city)
        states.append(state)
        zips.append(zipp)
        country_codes.append(country_code)
        store_numbers.append(store_number)
        phones.append(phone)
        location_types.append(location_type)
        latitudes.append(latitude)
        longitudes.append(longitude)
        hours_of_operations.append(hours)

        current_coords = [latitude, longitude]
        coords.append(current_coords)


def getdata(start_num, search_code):
    print("new_go")
    driver = SgChrome(executable_path="chromedriver.exe", is_headless=True).driver()
    driver.get(base_url)

    html = driver.page_source
    soup = bs(html, "html.parser")
    with open('page_source.txt', 'w', encoding='utf-8') as f:
        print(soup, file=f)

    scripts = soup.find_all("script")
    # print(len(scripts))
    for script in scripts:
        try:
            if "Incapsula" in script["src"]:
                incap_str = script["src"]
                break
        except Exception:
            #print(script)
            pass

    try:
        incap_url = base_url + incap_str
    except Exception:
        incap_str = "/_Incapsula_Resource?SWJIYLWA=719d34d31c8e3a6e6fffd425f7e032f3"
        incap_url = base_url + incap_str

    s.get(incap_url)

    for x in range(100):
        if x < start_num:
            pass
        else:
            
            failed = 0
            for request in driver.requests:
                    print(x)
                    
                    data_url = "https://www.rackroomshoes.com/store-finder?q=" + search_code + "&page=" + str(x)

                    headers = request.headers
                    
                    try:
                        response = s.get(data_url, headers=headers)
                        response_text = response.text
                        response_json = response.json()
                    except Exception:
                        continue

                    r_list = response_text.split("displayName")

                    if len(r_list) > 2:

                        with open('file_' + str(x) + '.txt', 'w', encoding='utf-8') as f:
                            print(response, file=f)

                        parse_response(response_json, data_url)

                        print("SUCCESS")
                        failed = 1
                        break
            
            if failed == 0:
                return x

    return x


for zipcode in search:
    failed_num = 0
    coords = []
    while failed_num <99:

        prev_fail = failed_num
        failed_num = getdata(failed_num, zipcode)

        if prev_fail == failed_num:
            break
    search.mark_found(coords)


df = pd.DataFrame(
    {
        "locator_domain": locator_domains,
        "page_url": page_urls,
        "location_name": location_names,
        "street_address": street_addresses,
        "city": citys,
        "state": states,
        "zip": zips,
        "store_number": store_numbers,
        "phone": phones,
        "latitude": latitudes,
        "longitude": longitudes,
        "hours_of_operation": hours_of_operations,
        "country_code": country_codes,
        "location_type": location_types,
    }
)

df = df.fillna("<MISSING>")
df = df.replace(r"^\s*$", "<MISSING>", regex=True)

df["dupecheck"] = (
    df["location_name"]
    + df["street_address"]
    + df["city"]
    + df["state"]
    + df["location_type"]
)

df = df.drop_duplicates(subset=["dupecheck"])
df = df.drop(columns=["dupecheck"])
df = df.replace(r"^\s*$", "<MISSING>", regex=True)
df = df.fillna("<MISSING>")

df.to_csv("data.csv", index=True)
