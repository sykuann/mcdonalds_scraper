# McDonald's Malaysia Location Scraper

This project scrapes McDonald's outlet information from the official McDonald's Malaysia website and provides a web interface with chatbot capabilities to query the data.

## Features

- Scrapes McDonald's outlet information for Kuala Lumpur
- Extracts outlet names, addresses, operating hours, and Waze links
- Handles pagination automatically
- Stores data in SQLite database
- Web interface for viewing and searching outlets
- Chatbot interface for natural language queries
- Geocoding support for location-based queries
- Includes error handling and logging

## Project Structure

```
mcdonalds_scraper/
├── src/
│   ├── api/              # API endpoints
│   │   ├── api.py        # Main API server
│   │   └── chatbot_api.py # Chatbot API server
│   ├── scraper/          # Scraping functionality
│   │   └── scraper.py    # Main scraper script
│   ├── database/         # Database operations
│   │   └── database.py   # Database utilities
│   ├── utils/           # Utility scripts
│   │   ├── geocode_outlets.py
│   │   ├── local_llm.py
│   │   ├── sql_queries.py
│   │   └── download_model.py
│   └── frontend/        # Frontend files
│       └── index.html   # Web interface
├── models/             # Local LLM models
├── logs/              # Application logs
├── requirements.txt   # Python dependencies
└── .env              # Environment variables
```

## Prerequisites

- Python 3.8 or higher
- Chrome browser installed
- pip (Python package manager)
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sykuann/mcdonalds_scraper.git
cd mcdonalds_scraper
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate     # On Unix/MacOS
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Download the LLM model:
```bash
python src/utils/download_model.py
```

5. Set up environment variables:
Create a `.env` file with the following variables:
```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Running the Scraper

To scrape McDonald's outlet data:

1. Make sure you're in the project root directory and your virtual environment is activated:
```bash
# If not already activated, activate the virtual environment
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate     # On Unix/MacOS
```

2. Install required packages if not already installed:
```bash
pip install -r requirements.txt
```

3. Set up the Python path to include the project root:
```bash
# On Unix/MacOS
export PYTHONPATH=$PYTHONPATH:$(pwd)

# On Windows (Git Bash)
export PYTHONPATH=$PYTHONPATH:$(pwd)
# or
set PYTHONPATH=%PYTHONPATH%;%CD%
```

4. Run the scraper from the project root:
```bash
python src/scraper/scraper.py
```

The scraper will:
- Launch a headless Chrome browser
- Navigate to the McDonald's Malaysia location page
- Filter for Kuala Lumpur locations
- Scrape all outlet information including:
  - Outlet names
  - Addresses
  - Operating hours
  - Waze links
- Store the data in `mcdonalds_outlets.db`

Note: The scraper includes rate limiting and delays to prevent overwhelming the website. The process may take several minutes to complete.

## Usage

1. Start the main API server:
```bash
cd src/api
python api.py
```

2. Start the chatbot API server (in a new terminal):
```bash
cd src/api
python chatbot_api.py
```

3. Start the frontend server (in a new terminal):
```bash
cd src/frontend
python -m http.server 8080
```

4. Access the application:
- Main API: http://localhost:8000
- Chatbot API: http://localhost:8001
- Web Interface: http://localhost:8080

## Database Schema

The data is stored in a SQLite database with the following schema:

```sql
CREATE TABLE outlets (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(500) NOT NULL,
    operating_hours VARCHAR(255),
    waze_link VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Features in Detail

### Scraping
- Automated scraping of McDonald's Malaysia website
- Handles dynamic content loading
- Includes rate limiting and error handling
- Stores data in SQLite database

### Web Interface
- Modern, responsive design
- Search functionality
- Interactive map view
- Detailed outlet information display

### Chatbot
- Natural language processing capabilities
- Location-based queries
- Operating hours information
- Address and contact details

### Geocoding
- Address to coordinates conversion
- Distance-based search
- Location-based filtering

## Error Handling

The application includes comprehensive error handling and logging:
- All operations are logged to the console and log files
- Errors are caught and logged with appropriate messages
- Database transactions are properly managed with rollback on errors
- API endpoints include proper error responses

## Notes

- The scraper runs Chrome in headless mode by default
- There are appropriate delays between actions to prevent overwhelming the website
- The application respects the website's structure and includes proper waiting mechanisms
- Local LLM models are stored in the `models/` directory
- Logs are stored in the `logs/` directory

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
