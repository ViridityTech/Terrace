from simple_salesforce import Salesforce
import pandas as pd
import configparser
import os

# Function to load credentials from file
def load_credentials():
    creds = {
        "username": "",
        "password": "",
        "security_token": ""
    }
    
    # Check if credentials file exists
    if os.path.isfile('credentials.ini'):
        config = configparser.ConfigParser()
        config.read('credentials.ini')
        
        if 'salesforce' in config:
            sf_config = config['salesforce']
            creds["username"] = sf_config.get('username', '')
            creds["password"] = sf_config.get('password', '')
            creds["security_token"] = sf_config.get('security_token', '')
    
    return creds

def explore_salesforce_fields():
    # Load credentials
    creds = load_credentials()
    
    if not all([creds["username"], creds["password"], creds["security_token"]]):
        print("Please provide credentials in credentials.ini file")
        username = input("Enter Salesforce username: ")
        password = input("Enter Salesforce password: ")
        security_token = input("Enter Salesforce security token: ")
    else:
        username = creds["username"]
        password = creds["password"]
        security_token = creds["security_token"]
    
    print(f"Connecting to Salesforce as {username}...")
    
    try:
        # Connect to Salesforce
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain='login'
        )
        print("Connected successfully!")
        
        # Get description of Lead object
        print("Retrieving Lead object description...")
        lead_desc = sf.Lead.describe()
        
        # Extract field information
        fields = []
        for field in lead_desc['fields']:
            fields.append({
                'name': field['name'],
                'label': field['label'],
                'type': field['type'],
                'custom': field['custom']
            })
        
        # Convert to DataFrame for easier viewing
        fields_df = pd.DataFrame(fields)
        
        # Save all fields to CSV
        fields_df.to_csv('salesforce_lead_fields.csv', index=False)
        print(f"Saved {len(fields_df)} fields to salesforce_lead_fields.csv")
        
        # Display custom fields (which might include the lead ID field)
        custom_fields = fields_df[fields_df['custom'] == True]
        print("\nCustom Fields (potential lead ID fields):")
        for _, row in custom_fields.iterrows():
            print(f"- {row['name']} ({row['label']}, Type: {row['type']})")
        
        # Try to identify potential ID fields
        id_fields = fields_df[fields_df['name'].str.contains('id|Id|ID|lead|Lead|LEAD', case=False)]
        print("\nPotential ID fields:")
        for _, row in id_fields.iterrows():
            print(f"- {row['name']} ({row['label']}, Type: {row['type']}, Custom: {row['custom']})")
        
        # Try a sample query with a few records
        print("\nRetrieving sample Lead record to inspect structure...")
        sample = sf.query("SELECT Id, CreatedDate FROM Lead LIMIT 1")
        if 'records' in sample and sample['records']:
            print("Sample record keys:", sample['records'][0].keys())
            print("Record detail:", sample['records'][0])
        else:
            print("No sample records found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def get_leads_for_month(sf, start_date, end_date):
    valid_locations = get_valid_locations()
    # Escape single quotes in location names
    escaped_locations = [loc.replace("'", "\\'") for loc in valid_locations]
    location_filter = "', '".join(escaped_locations)
    
    query = f"""
    SELECT 
        X18_Digit_ID__c,
        pi_Lead__c,
        CreatedDate, 
        Media_Location_Text__c,
        COUNT(Id) lead_count
    FROM Lead
    WHERE 
        CreatedDate >= {start_date} AND 
        CreatedDate <= {end_date} AND
        Media_Location_Text__c IN ('{location_filter}')
    GROUP BY 
        X18_Digit_ID__c,
        pi_Lead__c,
        CreatedDate, 
        Media_Location_Text__c
    ORDER BY 
        CreatedDate ASC
    """
    
    try:
        result = sf.query_all(query)
        return pd.DataFrame(result['records'])
    except Exception as e:
        print(f"Query error: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    explore_salesforce_fields()