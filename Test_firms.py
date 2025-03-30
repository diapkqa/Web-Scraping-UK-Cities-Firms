import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.maximize_window()

# Base URL
URL = "https://find.icaew.com/"
all_data = []
cities = [
    "Leeds", "Glasgow", "Manchester", "Sheffield", "Bradford", "Edinburgh", "Liverpool", "Bristol",
    "Cardiff", "Leicester", "Coventry", "Wakefield", "Belfast", "Nottingham", "Newcastle", "Doncaster",
    "Milton Keynes", "Salford", "Sunderland", "Brighton and Hove", "Wolverhampton", "Kingston upon Hull",
    "Plymouth", "Derby", "Stoke", "Southampton", "Swansea", "Aberdeen", "Peterborough", "Portsmouth",
    "York", "Colchester", "Chelmsford", "Oxford", "Newport", "Canterbury", "Preston", "Dundee", "Cambridge",
    "St Albans", "Lancaster", "Norwich", "Chester", "Exeter", "Wrexham", "Gloucester", "Winchester",
    "Durham", "Carlisle", "Worcester", "Lincoln", "Bath", "Salisbury", "Lichfield", "Chichester"
]



def get_firm_details():
    """Extracts firm details from the current firm page."""
    soup = BeautifulSoup(driver.page_source, "html.parser")
    details = {"Address": "Not available", "Telephone": "Not available",
               "Website": "Not available", "Email Address": "Not available",
               "ICAEW Chartered Accountants": "N/A"}
    try:
        details_div = soup.select_one("div.large-6.columns.component")
        if details_div:
            dt_elements = details_div.select("dt")
            dd_elements = details_div.select("dd")
            for dt, dd in zip(dt_elements, dd_elements):
                key, value = dt.text.strip(), dd.text.strip()
                details[key] = value
    except Exception as e:
        print(f"Error fetching firm details: {e}")
    return details


def scrape_city(city):
    print(f"Scraping firms in {city}...")
    driver.get(URL)
    wait = WebDriverWait(driver, 20)

    try:
        accept_cookies = wait.until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")))
        accept_cookies.click()
    except:
        pass

    search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="location_freetext"]')))
    search_box.clear()
    search_box.send_keys(city)
    search_button = driver.find_element(By.CSS_SELECTOR, "button.split-search__button[type='submit']")
    search_button.click()

    page_number = 1
    while True:
        print(f"Scraping page {page_number} for {city}...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#results div ul li')))
        firms = driver.find_elements(By.CSS_SELECTOR, '#results div ul li')

        for index in range(len(firms)):
            try:
                firms = driver.find_elements(By.CSS_SELECTOR, '#results div ul li')  # Refetch elements
                if index >= len(firms):
                    break

                more_info_buttons = firms[index].find_elements(By.CSS_SELECTOR, "a.card-link")
                if not more_info_buttons:
                    continue

                more_info_button = more_info_buttons[0]
                driver.execute_script("arguments[0].scrollIntoView();", more_info_button)
                driver.execute_script("arguments[0].click();", more_info_button)
                time.sleep(1)

                firm_name = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
                icaew_element = driver.find_elements(By.CSS_SELECTOR, ".list-group-item")
                ICAEW_Chartered_Accountants = icaew_element[0].text.strip() if icaew_element else "N/A"
                extra_details = get_firm_details()

                all_data.append({
                    "Firm Name": firm_name,
                    "Address": extra_details["Address"],
                    "Telephone": extra_details["Telephone"],
                    "Website": extra_details["Website"],
                    "Email Address": extra_details["Email Address"],
                    "ICAEW Chartered Accountants": ICAEW_Chartered_Accountants
                })

                driver.back()
                time.sleep(2)

            except Exception as e:
                print(f"Error extracting firm details: {e}")


        try:
            next_button = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Next")))
            driver.execute_script("arguments[0].click();", next_button)
            page_number += 1
            time.sleep(2)
        except:
            print(f"Finished scraping {city}!")
            break


for city in cities:
    scrape_city(city)

df = pd.DataFrame(all_data)
df.to_excel("ICAEW_Firms_Final_List_Appended_Three_Cities_Here.xlsx", index=False)
driver.quit()
print("Scraping completed! Data saved.")
