from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
from src.database.database import Database
from selenium.webdriver.support.ui import Select
import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class McDonaldsScraper:
    def __init__(self):
        self.url = "https://www.mcdonalds.com.my/locate-us"
        self.db = Database()
        self.setup_driver()
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in environment variables")

    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")  # Added for Windows compatibility
        
        try:
            # Use the specific ChromeDriver path
            driver_path = r"C:\Users\sykua\.wdm\drivers\chromedriver\win64\134.0.6998.165\chromedriver-win64\chromedriver.exe"
            
            if os.path.exists(driver_path):
                logger.info(f"Using ChromeDriver at: {driver_path}")
            else:
                logger.error(f"ChromeDriver not found at: {driver_path}")
                raise FileNotFoundError(f"ChromeDriver not found at: {driver_path}")
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up ChromeDriver: {str(e)}")
            raise

    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present on the page."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {value}")
            return None

    def filter_by_location(self, location="Kuala Lumpur"):
        """Filter the search by location."""
        try:
            # Wait for the container with the location inputs
            location_container = self.wait_for_element(By.CSS_SELECTOR, "div.location_inputs")
            if not location_container:
                logger.error("Location container not found")
                return False

            # Find the states dropdown within the container
            states_dropdown = location_container.find_element(By.ID, "states")
            if not states_dropdown:
                logger.error("States dropdown not found")
                return False

            # Click the dropdown to expand it
            states_dropdown.click()
            time.sleep(1)  # Wait for dropdown to expand

            # Wait for and click the specific option
            kuala_lumpur_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//select[@id='states']/option[normalize-space()='{location}']")
                )
            )
            kuala_lumpur_option.click()
            
            # Wait for results to load
            time.sleep(5)
            
            # Wait for any loading indicators to disappear
            try:
                WebDriverWait(self.driver, 10).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".loading-indicator"))
                )
            except TimeoutException:
                pass  # No loading indicator found, continue
            
            logger.info(f"Successfully selected location: {location}")
            return True

        except Exception as e:
            logger.error(f"Error filtering by location: {str(e)}")
            return False

    def get_location_details(self, place_name):
        """Get location details from Google Maps API."""
        try:
            # Remove " DT" from the place name if present
            if " DT" in place_name:
                place_name = place_name.replace(" DT", "")

            # Replace spaces with plus signs for URL formatting
            place_formatted = place_name.replace(" ", "+")
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_formatted}&key={self.api_key}"

            # First request: Geocoding API to get latitude, longitude, and place_id
            response = requests.get(geocode_url).json()

            if response["status"] == "OK":
                lat = response["results"][0]["geometry"]["location"]["lat"]
                lon = response["results"][0]["geometry"]["location"]["lng"]
                place_id = response["results"][0]['place_id']
                
                # Second request: Place Details API to get operating hours
                details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=opening_hours&key={self.api_key}"
                details_response = requests.get(details_url).json()
                
                operating_hours = []
                if details_response["status"] == "OK" and "opening_hours" in details_response["result"]:
                    operating_hours = details_response["result"]["opening_hours"].get("weekday_text", [])
                
                return {
                    'latitude': lat,
                    'longitude': lon,
                    'operating_hours': operating_hours
                }
            else:
                logger.warning(f"Error getting location details for {place_name}: {response.get('error_message', response.get('status'))}")
                return None
        except Exception as e:
            logger.error(f"Error in get_location_details: {str(e)}")
            return None

    def extract_outlet_data(self):
        """Extract data from the current page of results."""
        outlets = []
        try:
            # Wait for outlet cards to load with increased timeout
            outlet_cards = self.wait_for_element(By.CSS_SELECTOR, "div.addressTop", timeout=30)
            if not outlet_cards:
                logger.error("No outlet cards found on the page")
                return outlets

            # Find all outlet cards
            cards = self.driver.find_elements(By.CSS_SELECTOR, "div.addressTop")
            logger.info(f"Found {len(cards)} outlet cards on the page")
            
            for card in cards:
                try:
                    # Extract branch name
                    branch_name = card.find_element(By.CSS_SELECTOR, "a.addressTitle strong").text.strip()
                    
                    # Extract address and telephone
                    address_elements = card.find_elements(By.CSS_SELECTOR, "p.addressText")
                    address = address_elements[0].text.strip() if len(address_elements) > 0 else "Address not found"
                    telephone = address_elements[1].text.strip() if len(address_elements) > 1 else "Telephone not found"
                    
                    # Extract facilities
                    facility_elements = card.find_elements(
                        By.XPATH, ".//a[contains(@class, 'ed-tooltip')]/span[contains(@class, 'ed-tooltiptext')]"
                    )
                    facilities = []
                    for facility in facility_elements:
                        text = facility.get_attribute("textContent").strip()
                        facilities.append(text)
                    
                    # Get location details from Google Maps API
                    location_details = self.get_location_details(branch_name)
                    
                    outlet_data = {
                        'name': branch_name,
                        'address': address,
                        'telephone': telephone,
                        'facilities': facilities,
                        'latitude': location_details['latitude'] if location_details else None,
                        'longitude': location_details['longitude'] if location_details else None,
                        'operating_hours': location_details['operating_hours'] if location_details else []
                    }
                    outlets.append(outlet_data)
                    logger.info(f"Successfully extracted data for outlet: {outlet_data['name']}")
                    
                    # Add a small delay to avoid hitting API rate limits
                    time.sleep(0.5)
                    
                except NoSuchElementException as e:
                    logger.warning(f"Could not extract all data from an outlet card: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error extracting outlet data: {str(e)}")
        
        return outlets

    def has_next_page(self):
        """Check if there is a next page of results."""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, ".pagination-next:not(.disabled)")
            return next_button.is_displayed()
        except NoSuchElementException:
            return False

    def go_to_next_page(self):
        """Navigate to the next page of results."""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, ".pagination-next:not(.disabled)")
            next_button.click()
            time.sleep(2)  # Wait for new results to load
            return True
        except Exception as e:
            logger.error(f"Error navigating to next page: {str(e)}")
            return False

    def scrape_all_outlets(self):
        """Main method to scrape all outlets."""
        try:
            self.driver.get(self.url)
            time.sleep(3)  # Wait for page to load

            if not self.filter_by_location():
                logger.error("Failed to filter by location")
                return

            while True:
                outlets = self.extract_outlet_data()
                for outlet in outlets:
                    self.db.insert_outlet(outlet)
                
                if not self.has_next_page():
                    break
                
                if not self.go_to_next_page():
                    break

        except Exception as e:
            logger.error(f"Error in main scraping process: {str(e)}")
        finally:
            self.driver.quit()
            self.db.close()

if __name__ == "__main__":
    scraper = McDonaldsScraper()
    scraper.scrape_all_outlets() 