import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# Configure Chrome options

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--headless")  # Enable for production
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")


# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)
driver.maximize_window()
wait = WebDriverWait(driver, 30)

# Constants
BASE_URL = "https://find.icaew.com/"
CITIES = ["London", "Birmingham", "Leeds", "Glasgow", "Manchester", "Sheffield", "Bradford", "Edinburgh",
    "Liverpool"]
all_firm_data = []
""", "Bristol", "Cardiff", "Leicester", "Coventry", "Wakefield",
    "Belfast", "Nottingham", "Newcastle", "Doncaster", "Milton Keynes",
    "Salford", "Sunderland", "Brighton and Hove", "Wolverhampton",
    "Kingston upon Hull", "Derby", "Stoke", "Southampton", "Swansea",
    "Aberdeen", "Peterborough", "Portsmouth", "York", "Colchester",
    "Chelmsford", "Oxford", "Newport", "Canterbury", "Preston", "Dundee",
    "Cambridge", "St Albans", "Lancaster", "Norwich", "Chester", "Exeter",
    "Wrexham", "Gloucester", "Winchester", "Carlisle", "Salisbury",
    "Lichfield", "Chichester"""

def accept_cookies():
    try:
        accept_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
        )
        accept_btn.click()
        print("Cookies accepted")
    except Exception:
        pass


def search_firms_by_city(city):
    print(f"\nStarting search for firms in {city}...")
    driver.get(BASE_URL)
    accept_cookies()

    # Perform search
    search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="location_freetext"]')))
    search_box.clear()
    search_box.send_keys(city)
    search_btn = driver.find_element(By.CSS_SELECTOR, "button.split-search__button[type='submit']")
    search_btn.click()
    time.sleep(3)  # Wait for results


def process_all_pages():
    processed_urls = set()
    page_count = 1

    while True:
        print(f"\nProcessing page {page_count}...")

        try:
            # Wait for results and get firm cards
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.search-results')))
            firm_cards = driver.find_elements(By.CSS_SELECTOR, 'ul.search-results > li')
            print(f"Found {len(firm_cards)} firms on this page")

            # Process each firm on current page
            for index in range(len(firm_cards)):
                try:
                    # Refresh references to avoid staleness
                    firm_cards = driver.find_elements(By.CSS_SELECTOR, 'ul.search-results > li')
                    card = firm_cards[index]

                    # Get firm URL from card
                    more_info_link = card.find_element(By.CSS_SELECTOR, "a.card-link")
                    firm_url = more_info_link.get_attribute("href")

                    # Skip if already processed
                    if firm_url in processed_urls:
                        print(f"Skipping already processed firm: {firm_url}")
                        continue

                    processed_urls.add(firm_url)

                    # Click the firm link
                    print(f"\nProcessing firm {index + 1}/{len(firm_cards)}...")
                    more_info_link.click()

                    # Scrape firm details
                    firm_data = scrape_firm_details()
                    if firm_data:
                        firm_data["Page Number"] = page_count
                        all_firm_data.append(firm_data)

                    # Return to search results
                    driver.back()
                    time.sleep(2)  # Wait for results to reload

                    # Wait for results to be present again
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.search-results')))

                except StaleElementReferenceException:
                    print("Stale element reference, retrying...")
                    continue
                except Exception as e:
                    print(f"Error processing firm {index + 1}: {str(e)}")
                    if "search" not in driver.current_url.lower():
                        driver.back()
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.search-results')))
                    continue

            # Try to click Next button
            try:
                next_button = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Next")))

                # Check if Next button is disabled
                if "disabled" in next_button.get_attribute("class"):
                    print("Reached last page")
                    break

                # Scroll to pagination and click Next
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                next_button.click()
                page_count += 1
                time.sleep(3)  # Wait for new page to load

                # Wait for URL to change
                wait.until(lambda d: "page=" in d.current_url)

            except (NoSuchElementException, TimeoutException):
                print("No more pages available")
                break

        except Exception as e:
            print(f"Error processing page {page_count}: {str(e)}")
            break


def scrape_firm_details():
    try:
        # Wait for firm page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'h1')))
        time.sleep(1)  # Additional stability wait

        # Initialize data dict
        firm_data = {
            "Firm Name": driver.find_element(By.TAG_NAME, 'h1').text.strip(),
            "Firm URL": driver.current_url,
            "Address": "N/A",
            "Telephone": "N/A",
            "Website": "N/A",
            "Email": "N/A",
            "Services": "N/A",
            "Accountants": "N/A",
            "Page Number": "N/A"
        }

        # Extract address if available
        try:
            address_element = driver.find_element(By.XPATH, "//dt[text()='Address']/following-sibling::dd")
            firm_data["Address"] = address_element.text.strip()
        except NoSuchElementException:
            firm_data["Address"] = "Not available"

        # Extract contact details
        try:
            contact_section = wait.until(
                EC.presence_of_element_located((By.XPATH, '//h2[contains(text(),"Contact")]/following-sibling::dl'))
            )

            # Process all contact items
            items = contact_section.find_elements(By.XPATH, './dt')
            for dt in items:
                label = dt.text.strip()
                dd = dt.find_element(By.XPATH, './following-sibling::dd[1]')

                if label == "Telephone":
                    firm_data["Telephone"] = dd.text.strip()
                elif label == "Website":
                    try:
                        firm_data["Website"] = dd.find_element(By.TAG_NAME, 'a').text.strip()
                    except:
                        firm_data["Website"] = dd.text.strip()
                elif label == "Email address":
                    try:
                        firm_data["Email"] = dd.find_element(By.CSS_SELECTOR, 'a[href^="mailto:"]').text.strip()
                    except:
                        firm_data["Email"] = dd.text.strip() if dd.text.strip() else "Not available"

        except Exception as e:
            print(f"Couldn't extract contact details: {str(e)}")

        # Extract services
        try:
            services_section = driver.find_element(By.CSS_SELECTOR, 'div.profile-services')
            services = [s.text.strip() for s in services_section.find_elements(By.CSS_SELECTOR, 'span.label')]
            firm_data["Services"] = ", ".join(services) if services else "N/A"
        except NoSuchElementException:
            pass

        # Extract ICAEW accountants
        try:
            accountants_section = wait.until(
                EC.presence_of_element_located((By.XPATH, '//h2[contains(text(),"ICAEW")]/following-sibling::ul'))
            )
            accountants = [a.text.strip() for a in accountants_section.find_elements(By.CSS_SELECTOR, 'h3 a')]
            firm_data["Accountants"] = ", ".join(accountants) if accountants else "N/A"
        except TimeoutException:
            pass

        return firm_data

    except Exception as e:
        print(f"Error scraping firm details: {str(e)}")
        return None


# Main execution
try:
    for city in CITIES:
        search_firms_by_city(city)
        process_all_pages()

    # Save results to Excel
    if all_firm_data:
        df = pd.DataFrame(all_firm_data)

        # Clean and organize data
        df.drop_duplicates(subset=["Firm URL"], keep='first', inplace=True)
        column_order = [
            "Firm Name", "Address", "Telephone", "Website", "Email",
            "Services", "Accountants", "Page Number", "Firm URL"
        ]
        df = df[column_order]

        output_file = "ICAEW_Final_Firms_List_1.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\nSuccess! Saved {len(df)} firms from all pages to {output_file}")
    else:
        print("\nNo firm data was collected")

finally:
    driver.quit()


