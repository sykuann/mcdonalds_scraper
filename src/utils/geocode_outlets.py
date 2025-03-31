from database import Database
import requests
import time
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Geocoder:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not found in environment variables")
        self.db = Database()

    def geocode_address(self, address):
        """Get coordinates for a given address using Google Maps Geocoding API."""
        try:
            # Format address for URL
            formatted_address = address.replace(" ", "+")
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={formatted_address}&key={self.api_key}"
            
            response = requests.get(url)
            data = response.json()
            
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                return {
                    'latitude': location['lat'],
                    'longitude': location['lng']
                }
            else:
                logger.warning(f"Geocoding failed for address: {address}. Status: {data['status']}")
                return None
                
        except Exception as e:
            logger.error(f"Error geocoding address {address}: {str(e)}")
            return None

    def update_outlet_coordinates(self, outlet_id, coordinates):
        """Update the coordinates for a specific outlet in the database."""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                UPDATE outlets 
                SET latitude = ?, longitude = ?
                WHERE id = ?
            ''', (coordinates['latitude'], coordinates['longitude'], outlet_id))
            self.db.conn.commit()
            logger.info(f"Updated coordinates for outlet ID {outlet_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating coordinates for outlet ID {outlet_id}: {str(e)}")
            self.db.conn.rollback()
            return False

    def process_outlets(self):
        """Process all outlets that need geocoding."""
        try:
            # Get all outlets without coordinates
            cursor = self.db.conn.cursor()
            cursor.execute('SELECT id, name, address FROM outlets WHERE latitude IS NULL OR longitude IS NULL')
            outlets = cursor.fetchall()
            
            if not outlets:
                logger.info("No outlets need geocoding.")
                return
            
            logger.info(f"Found {len(outlets)} outlets that need geocoding.")
            
            # Process each outlet
            for outlet_id, name, address in outlets:
                logger.info(f"Processing outlet: {name}")
                
                # Add "Malaysia" to the address for better geocoding results
                full_address = f"{address}, Malaysia"
                
                # Get coordinates
                coordinates = self.geocode_address(full_address)
                
                if coordinates:
                    # Update database
                    if self.update_outlet_coordinates(outlet_id, coordinates):
                        logger.info(f"Successfully geocoded outlet: {name}")
                    else:
                        logger.error(f"Failed to update coordinates for outlet: {name}")
                else:
                    logger.warning(f"Could not geocode outlet: {name}")
                
                # Add delay to avoid hitting API rate limits
                time.sleep(0.5)
            
            # Print summary
            cursor.execute('SELECT COUNT(*) FROM outlets WHERE latitude IS NULL OR longitude IS NULL')
            remaining = cursor.fetchone()[0]
            logger.info(f"Geocoding complete. {remaining} outlets still need coordinates.")
            
        except Exception as e:
            logger.error(f"Error processing outlets: {str(e)}")
        finally:
            self.db.close()

def main():
    """Main function to run the geocoding process."""
    try:
        geocoder = Geocoder()
        geocoder.process_outlets()
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main() 