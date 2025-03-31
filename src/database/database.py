import sqlite3
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('mcdonalds_outlets.db')
        self.create_tables()

    def create_tables(self):
        """Create the necessary tables if they don't exist."""
        try:
            cursor = self.conn.cursor()
            
            # Create outlets table with updated schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outlets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    telephone TEXT,
                    latitude REAL,
                    longitude REAL,
                    facilities TEXT,
                    operating_hours TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    def insert_outlet(self, outlet_data):
        """Insert a new outlet into the database."""
        try:
            cursor = self.conn.cursor()
            
            # Convert facilities and operating_hours lists to JSON strings
            facilities_json = json.dumps(outlet_data.get('facilities', []))
            operating_hours_json = json.dumps(outlet_data.get('operating_hours', []))
            
            cursor.execute('''
                INSERT INTO outlets (
                    name, address, telephone, latitude, longitude, 
                    facilities, operating_hours
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                outlet_data['name'],
                outlet_data['address'],
                outlet_data.get('telephone'),
                outlet_data.get('latitude'),
                outlet_data.get('longitude'),
                facilities_json,
                operating_hours_json
            ))
            
            self.conn.commit()
            logger.info(f"Successfully inserted outlet: {outlet_data['name']}")
        except Exception as e:
            logger.error(f"Error inserting outlet: {str(e)}")
            self.conn.rollback()
            raise

    def get_all_outlets(self):
        """Retrieve all outlets from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM outlets')
            rows = cursor.fetchall()
            
            # Convert the rows to dictionaries with proper JSON parsing
            outlets = []
            for row in rows:
                outlet = {
                    'id': row[0],
                    'name': row[1],
                    'address': row[2],
                    'telephone': row[3],
                    'latitude': row[4],
                    'longitude': row[5],
                    'facilities': json.loads(row[6]) if row[6] else [],
                    'operating_hours': json.loads(row[7]) if row[7] else [],
                    'created_at': row[8]
                }
                outlets.append(outlet)
            
            return outlets
        except Exception as e:
            logger.error(f"Error retrieving outlets: {str(e)}")
            return []

    def close(self):
        """Close the database connection."""
        try:
            self.conn.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}") 