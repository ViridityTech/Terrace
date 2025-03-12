# Terrace

Terrace is a lead forecasting tool that uses time series analysis to predict future lead volumes for different locations based on historical Salesforce data.

![Orchard Logo](orchard_logo.png)

## Features

- Connect to Salesforce to retrieve historical lead data
- Generate lead forecasts for specific locations and time periods
- Visualize forecasts with interactive charts
- Export forecast results and visualizations as downloadable ZIP files
- Chain forecasting for future months based on predicted data

## Installation

### Prerequisites

- Python 3.8 or higher
- Salesforce account with API access
- Salesforce security token

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/Terrace.git
   cd Terrace
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Start the Streamlit application:

```
streamlit run terrece.py
```

This will launch the web interface in your default browser.

### Authentication

1. Enter your Salesforce credentials:
   - Username
   - Password
   - Security Token

2. Click "Connect to Salesforce" to authenticate.

### Generating Forecasts

1. Select a target month for the forecast
2. Choose a location (or "All Locations")
3. Click "Generate Forecast"

The application will:
- Retrieve historical lead data from Salesforce
- Process and prepare the data
- Generate forecasts using ARIMA time series models
- Display visualizations of the forecasts
- Provide a download option for the results

### Downloading Results

After generating forecasts, you can download a ZIP file containing:
- CSV file with forecast results
- PNG images of forecast visualizations for each location

## Project Structure

- `terrece.py` - Main Streamlit application
- `query.py` - Salesforce data retrieval functions
- `forecast.py` - Time series forecasting logic
- `requirements.txt` - Python dependencies
- `forecast_results/` - Directory for saved forecast CSV files
- `forecast_visuals/` - Directory for saved forecast visualizations

## Dependencies

Key dependencies include:
- streamlit - Web application framework
- pandas - Data manipulation
- statsmodels - Time series forecasting
- matplotlib - Data visualization
- simple-salesforce - Salesforce API integration

## License

This project is licensed under the terms included in the LICENSE file.