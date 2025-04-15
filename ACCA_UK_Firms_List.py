import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument("--headless")

driver = webdriver.Chrome(options=options)
driver.maximize_window()


"""""London", "Birmingham", "Manchester", "Liverpool", "Leeds",
    "Sheffield", "Bristol", "Newcastle upon Tyne", "Nottingham", "Leicester",
    "Southampton", "Portsmouth", "Coventry", "Bradford", "Wolverhampton",
    "Edinburgh", "Glasgow", "Aberdeen", "Dundee",
    "Cardiff", "Swansea", "Newport",
    "Belfast", "Londonderry"""""


cities = [
    "Manchester"]


URL = "https://www.accaglobal.com/gb/en/member/find-an-accountant/find-firm.html"


all_data = []

def scrape_city(city):
    print(f"Scraping firms in {city}...")

    driver.get(URL)
    wait = WebDriverWait(driver, 10)


    try:
        accept_cookies_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept_cookies_button.click()
        print("Accepted cookies.")
    except:
        print("No cookie popup found.")


    search_box = wait.until(EC.presence_of_element_located((By.ID, "location-field")))
    search_box.clear()
    search_box.send_keys(city)


    country_dropdown = driver.find_element(By.ID, "country")
    country_dropdown.send_keys("United Kingdom")


    search_button = driver.find_element(By.CSS_SELECTOR, "button.btn.btn-lg[type='submit']")
    search_button.click()


    try:
        results_per_page = wait.until(EC.presence_of_element_located((By.ID, "select")))
        select = Select(results_per_page)
        select.select_by_value("25")
        time.sleep(2)
        print("Set results per page to 25.")
    except Exception as e:
        print(f"Could not select 25 results per page: {e}")

    page_number = 1

    while True:
        print(f"Scraping page {page_number} for {city}...")


        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr[id^='rowId']")))


        firms = driver.find_elements(By.CSS_SELECTOR, "tbody tr[id^='rowId']")

        for firm in firms:
            try:

                firm_details = firm.find_element(By.XPATH, ".//td[h5/a[contains(@class, 'detailsLink')]]")
                firm_name = firm_details.find_element(By.XPATH, ".//h5/a").text.strip()


                raw_address = firm_details.get_attribute("innerHTML").split("<br>")
                raw_address = [part.strip() for part in raw_address if part.strip()]


                address_soup = BeautifulSoup(' '.join(raw_address), 'html.parser')
                cleaned_address = address_soup.get_text(separator=" ").strip()
                address_parts = [cleaned_address, firm_details.find_element(By.XPATH, ".//div").text.strip(),"United Kingdom"]
                full_address = ", ".join(address_parts)

                city_name = firm_details.find_element(By.XPATH, ".//div").text.strip()
                country = raw_address[-1] if len(raw_address) > 1 else "N/A"
                full_address = cleaned_address

            except Exception as e:
                print(f"Error extracting firm details: {e}")
                firm_name, full_address, city_name, country = "N/A", "N/A", "N/A", "N/A"

            try:
                contact_column = firm.find_element(By.XPATH, "./td[2]")
                contact_items = contact_column.find_elements(By.TAG_NAME, "li")

                email, phone, website = "N/A", "N/A", "N/A"
                for item in contact_items:
                    text = item.text.strip()
                    if "@" in text:
                        email = text
                    elif text.startswith("http") or text.startswith("www"):
                        website = text
                    else:
                        phone = text

            except:
                email, phone, website = "N/A", "N/A", "N/A"


            all_data.append({
                "Firm Name": firm_name,
                "Address": full_address,
                "City": city_name,
                "Email": email,
                "Phone": phone,
                "Website": website
            })

        try:
            next_button = driver.find_element(By.LINK_TEXT, "Next")
            if next_button.get_attribute("aria-disabled") == "true":
                print(f"Finished scraping {city}!")
                break  # No more pages
            else:
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                driver.execute_script("arguments[0].click();", next_button)
                page_number += 1
                wait.until(EC.staleness_of(firms[0]))
        except:
            print(f"Finished scraping {city}!")
            break


for city in cities:
    scrape_city(city)


df = pd.DataFrame(all_data)
df.to_excel("ACCA_Manchester.xlsx", index=False)


driver.quit()

print("Scraping completed! Data saved to ACCA_Firms_London.xlsx")
