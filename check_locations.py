from simple_salesforce import Salesforce
import pandas as pd
from query import get_salesforce_auth, get_valid_locations
import configparser
import os

def load_credentials():
    """Load Salesforce credentials from credentials.ini file"""
    creds = {
        "username": "",
        "password": "",
        "security_token": ""
    }
    
    if os.path.isfile('credentials.ini'):
        config = configparser.ConfigParser()
        config.read('credentials.ini')
        
        if 'salesforce' in config:
            sf_config = config['salesforce']
            creds["username"] = sf_config.get('username', '')
            creds["password"] = sf_config.get('password', '')
            creds["security_token"] = sf_config.get('security_token', '')
    
    return creds

def check_locations():
    """Check locations in Salesforce against valid locations list"""
    # Load credentials
    credentials = load_credentials()
    
    # Get Salesforce connection
    sf, error = get_salesforce_auth(
        credentials["username"],
        credentials["password"],
        credentials["security_token"]
    )
    
    if sf is None:
        print(f"Authentication failed: {error}")
        return
    
    # Get valid locations
    valid_locations = get_valid_locations()
    print("\nValid locations from code:")
    for loc in sorted(valid_locations):
        print(f"- {loc}")
    
    # Query all unique locations from Salesforce
    query = """
    SELECT Media_Location_Text__c
    FROM Lead
    WHERE Media_Location_Text__c != null
    GROUP BY Media_Location_Text__c
    ORDER BY Media_Location_Text__c
    """
    
    try:
        result = sf.query_all(query)
        df = pd.DataFrame(result['records'])
        
        if not df.empty:
            # Clean up the data
            df['Media_Location_Text__c'] = df['Media_Location_Text__c'].str.strip()
            
            # Get all unique locations
            all_locations = sorted(df['Media_Location_Text__c'].unique())
            
            print("\nAll locations found in Salesforce:")
            for loc in all_locations:
                print(f"- {loc}")
            
            # Find locations in Salesforce that aren't in valid_locations
            missing_locations = [loc for loc in all_locations if loc not in valid_locations]
            
            if missing_locations:
                print("\nLocations in Salesforce that aren't in valid_locations:")
                for loc in missing_locations:
                    print(f"- {loc}")
            
            # Find locations in valid_locations that aren't in Salesforce
            unused_locations = [loc for loc in valid_locations if loc not in all_locations]
            
            if unused_locations:
                print("\nLocations in valid_locations that aren't in Salesforce:")
                for loc in unused_locations:
                    print(f"- {loc}")
            
            if not missing_locations and not unused_locations:
                print("\nAll locations match perfectly!")
                
    except Exception as e:
        print(f"Error querying Salesforce: {str(e)}")

if __name__ == "__main__":
    check_locations() 