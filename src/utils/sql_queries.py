"""
SQL queries for filtering McDonald's outlets based on facilities.
"""

FACILITY_QUERIES = {
    "24 Hours": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Operating_Hours LIKE '%24 Hours%'
    LIMIT 10
    """,
    
    "Birthday Party": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Birthday Party%'
    LIMIT 10
    """,
    
    "Breakfast": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Breakfast%'
    LIMIT 10
    """,
    
    "Cashless Facility": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Cashless Facility%'
    LIMIT 10
    """,
    
    "Dessert Center": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Dessert Center%'
    LIMIT 10
    """,
    
    "McCafe": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%McCafe%'
    LIMIT 10
    """,
    
    "McDelivery": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%McDelivery%'
    LIMIT 10
    """,
    
    "WiFi": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%WiFi%'
    LIMIT 10
    """,
    
    "Digital Order Kiosk": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Digital Order Kiosk%'
    LIMIT 10
    """,
    
    "Drive-Thru": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Drive-Thru%'
    LIMIT 10
    """,
    
    "Electric Vehicle": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Electric Vehicle%'
    LIMIT 10
    """,
    
    "Surau": """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE Facilities LIKE '%Surau%'
    LIMIT 10
    """
}

# Example of combining multiple facilities
def get_outlets_with_facilities(facilities: list) -> str:
    """
    Generate SQL query for outlets with multiple facilities.
    
    Args:
        facilities: List of facility names to search for
        
    Returns:
        SQL query string
    """
    conditions = []
    for facility in facilities:
        if facility == "24 Hours":
            conditions.append("Operating_Hours LIKE '%24 Hours%'")
        else:
            conditions.append(f"Facilities LIKE '%{facility}%'")
    
    query = """
    SELECT Name, Address, Operating_Hours, Facilities 
    FROM outlets 
    WHERE """ + " AND ".join(conditions) + """
    LIMIT 10
    """
    return query 