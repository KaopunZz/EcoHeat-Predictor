import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import pandas as pd
import gspread
import geopandas as gpd
from google.oauth2.service_account import Credentials
from datetime import datetime
import time
import random
import requests

load_dotenv()

# Replace with your Airtable API key
API_KEY = 'pat8CNnLmUO8jzljI.98328487a28e5c869f8feee86846468f4578fd792f7afd514b840d5f16b07f57'

# Base ID for your Airtable base
BASE_ID = 'appnBXpYPubEOsUtN'

# Table IDs
TASK_TABLE_ID = 'tblirKQeTlSOR8TKU'
EMPLOYEE_TABLE_ID = 'tbljDoA0K6vnHoERM'
EMPLOYEE_TASK_TABLE_ID = 'tbl46HSl03qzB5tKF'

# Function to fetch records from a specific table
def fetch_records(table_id):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table_id}'
    headers = {
        'Authorization': f'Bearer {API_KEY}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return response.text
    
# Function to add a new record to a table
def add_record(table_id, record_data):
    url = f'https://api.airtable.com/v0/{BASE_ID}/{table_id}'
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, json={"fields": record_data}, headers=headers)
    return response.json()

def get_workbook():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(r"for-hotspot-ai-8d900a6cb5ce.json", scopes=scopes)
    client = gspread.authorize(creds)
    sheet_id = "1vkSq7e3rb2gcFI2OfIp7Vz_56-iju1CyKgmOcToXPPs"
    workbook = client.open_by_key(sheet_id)
    return workbook

def get_worksheet_names():
    workbook = get_workbook()
    worksheet_list = workbook.worksheets()
    worksheet_names = [worksheet.title for worksheet in worksheet_list]
    return worksheet_names

def get_worksheet_data(worksheet_name, max_retries=5):
    workbook = get_workbook()
    
    for attempt in range(max_retries):
        try:
            worksheet = workbook.worksheet(worksheet_name)
            
            # Get the header row
            headers = worksheet.row_values(1)
            
            # Check for unique headers
            if len(headers) != len(set(headers)):
                raise ValueError("The header row in the worksheet is not unique. Please ensure all column names are unique.")
            
            # Get all records
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            return df
        
        except gspread.exceptions.APIError as e:
            if e.response.status_code == 502:
                # Exponential backoff
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"Server error encountered. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Max retries exceeded")

# Custom CSS
custom_css = """
/* Main page styling */
body {
    color: #ffffff;
    background-color: #0e1117;
}

/* Sidebar styling */
.sidebar .sidebar-content {
    background-color: #1e2130;
}

/* Header styling */
h1, h2, h3 {
    color: #4da6ff;
    font-weight: bold;
}

/* Improve button styling */
.stButton > button {
    color: #ffffff;
    background-color: #4da6ff;
    border: none;
    border-radius: 5px;
    padding: 0.5rem 1rem;
    font-weight: bold;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background-color: #3385ff;
    box-shadow: 0 0 10px rgba(77, 166, 255, 0.5);
}

/* Style selectbox */
.stSelectbox > div > div {
    background-color: #1e2130;
    color: #ffffff;
}

/* Map container styling */
.folium-map {
    border: 2px solid #4da6ff;
    border-radius: 10px;
    overflow: hidden;
}

/* Risk area styling */
.risk-item {
    background-color: #1e2130;
    border-radius: 5px;
    padding: 1rem;
    margin-bottom: 3rem;
    transition: all 0.3s ease;
}

.risk-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(77, 166, 255, 0.2);
}

.risk-high {
    border-left: 4px solid #ff4d4d;
}

.risk-medium {
    border-left: 4px solid #ffa64d;
}

.risk-low {
    border-left: 4px solid #4dff4d;
}

/* Scrollable risk area */
.scrollable-risk-area {
    max-height: 600px;
    overflow-y: auto;
    padding-right: 1rem;
}

/* Custom metric display */
.metric-container {
    background-color: #1e2130;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 0 20px rgba(77, 166, 255, 0.1);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: #4da6ff;
}

.metric-label {
    font-size: 1rem;
    color: #a6a6a6;
}
"""

# All 77 Thai provinces with their approximate coordinates
THAI_PROVINCES = {
    "Amnat Charoen": (15.8661, 104.6289),
    "Ang Thong": (14.5896, 100.4549),
    "Bangkok": (13.7563, 100.5018),
    "Bueng Kan": (18.3609, 103.6466),
    "Buri Ram": (14.9951, 103.1116),
    "Chachoengsao": (13.6904, 101.0779),
    "Chai Nat": (15.1851, 100.1251),
    "Chaiyaphum": (15.8068, 102.0317),
    "Chanthaburi": (12.6100, 102.1034),
    "Chiang Mai": (18.7883, 98.9853),
    "Chiang Rai": (19.9105, 99.8406),
    "Chon Buri": (13.3611, 100.9847),
    "Chumphon": (10.4930, 99.1800),
    "Kalasin": (16.4315, 103.5059),
    "Kamphaeng Phet": (16.4827, 99.5226),
    "Kanchanaburi": (14.0023, 99.5328),
    "Khon Kaen": (16.4419, 102.8360),
    "Krabi": (8.0863, 98.9063),
    "Lampang": (18.2854, 99.5122),
    "Lamphun": (18.5743, 99.0087),
    "Loei": (17.4860, 101.7223),
    "Lop Buri": (14.7995, 100.6534),
    "Mae Hong Son": (19.2988, 97.9684),
    "Maha Sarakham": (16.0132, 103.1615),
    "Mukdahan": (16.5425, 104.7240),
    "Nakhon Nayok": (14.2069, 101.2130),
    "Nakhon Pathom": (13.8196, 100.0645),
    "Nakhon Phanom": (17.3948, 104.7692),
    "Nakhon Ratchasima": (14.9799, 102.0978),
    "Nakhon Sawan": (15.7030, 100.1371),
    "Nakhon Si Thammarat": (8.4304, 99.9631),
    "Nan": (18.7756, 100.7730),
    "Narathiwat": (6.4318, 101.8259),
    "Nong Bua Lam Phu": (17.2217, 102.4260),
    "Nong Khai": (17.8782, 102.7418),
    "Nonthaburi": (13.8622, 100.5140),
    "Pathum Thani": (14.0208, 100.5253),
    "Pattani": (6.8691, 101.2550),
    "Phang Nga": (8.4509, 98.5194),
    "Phatthalung": (7.6167, 100.0743),
    "Phayao": (19.2147, 100.2020),
    "Phetchabun": (16.4190, 101.1591),
    "Phetchaburi": (13.1119, 99.9438),
    "Phichit": (16.4398, 100.3489),
    "Phitsanulok": (16.8211, 100.2659),
    "Phra Nakhon Si Ayutthaya": (14.3692, 100.5876),
    "Phrae": (18.1445, 100.1405),
    "Phuket": (7.8804, 98.3923),
    "Prachin Buri": (14.0509, 101.3660),
    "Prachuap Khiri Khan": (11.8126, 99.7957),
    "Ranong": (9.9529, 98.6085),
    "Ratchaburi": (13.5282, 99.8134),
    "Rayong": (12.6815, 101.2816),
    "Roi Et": (16.0566, 103.6517),
    "Sa Kaeo": (13.8244, 102.0645),
    "Sakon Nakhon": (17.1664, 104.1486),
    "Samut Prakan": (13.5990, 100.5998),
    "Samut Sakhon": (13.5475, 100.2745),
    "Samut Songkhram": (13.4094, 100.0021),
    "Saraburi": (14.5289, 100.9109),
    "Satun": (6.6238, 100.0675),
    "Sing Buri": (14.8920, 100.3970),
    "Sisaket": (15.1185, 104.3229),
    "Songkhla": (7.1756, 100.6142),
    "Sukhothai": (17.0069, 99.8265),
    "Suphan Buri": (14.4744, 100.0913),
    "Surat Thani": (9.1351, 99.3268),
    "Surin": (14.8820, 103.4936),
    "Tak": (16.8840, 99.1259),
    "Trang": (7.5645, 99.6239),
    "Trat": (12.2428, 102.5179),
    "Ubon Ratchathani": (15.2448, 104.8472),
    "Udon Thani": (17.4156, 102.7872),
    "Uthai Thani": (15.3838, 100.0255),
    "Uttaradit": (17.6200, 100.0990),
    "Yala": (6.5414, 101.2803),
    "Yasothon": (15.7921, 104.1458)
}

def read_shapefile_data(file_path):
    return pd.read_csv(file_path)

def emission_calculation(rai):
    emission = 35.9 * rai * 10
    return emission

def display_farm_info(i, row, task_table, employee_table, employee_task_table, show_risk):
    
    if show_risk:
        color = 'white'
    else:
        color = 'rgb(255, 0, 0)' if row['risk'] == 1 else 'rgb(0, 255, 0)'
    tab1, tab2 = st.tabs(["Overview", "More Info"])
    
    with tab1:
        # risk_level = "high" if row['Risk'] > 66 else "medium" if row['Risk'] > 33 else "low"
        st.markdown(f"""
        <div class="risk-item">
            <h4 style="color:{color}">Farm {int(row['Id'])}</h4>
            <p><b>Prediction Date:</b> {row['predictdate']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        task_id = len(task_table) + 1
        st.session_state.selected_task_id = int(task_id)
        st.session_state.selected_farm_id = int(row['Id'])
        st.session_state.selected_predictdate = row['predictdate']
        st.session_state.selected_latitude = row['lat']
        st.session_state.selected_longitude = row['long']
        st.session_state.selected_rai = row['Shape_Area'] / 0.0016
        st.session_state.selected_yield = st.session_state.selected_rai * 10
        st.session_state.selected_emission = emission_calculation(st.session_state.selected_rai)

        task_record = {
            'TaskID': st.session_state.selected_task_id,
            'FarmID': st.session_state.selected_farm_id,
            'Location': f"{st.session_state.selected_latitude:.6f}, {st.session_state.selected_longitude:.6f}",
            'Priority': "P1",
            'Status': "In progress",
            'Start date': str(datetime.today().strftime("%Y-%m-%d")),
            'Possible Burn Date': str(datetime.strptime(row['predictdate'], "%d-%m-%Y")),
            'Note': "Default"
        }

        st.markdown("#### Information 👋")
        st.write(f"**Farm ID:** {st.session_state.selected_farm_id}")
        st.write(f"**Prediction Date:** {st.session_state.selected_predictdate}")
        st.write(f"**Latitude:** {st.session_state.selected_latitude:.3f}")
        st.write(f"**Longitude:** {st.session_state.selected_longitude:.3f}")
        st.write(f"**Emission:** {st.session_state.selected_emission:.2f} kg CO2e")
        st.write(f"**Area:** {st.session_state.selected_rai:.2f} rais")
        st.write(f"**Average Yield:** {st.session_state.selected_yield:.2f} tons")
        
        # If the farm id in the current row is already in the task table, display the responsible persons
        if not task_table.empty and st.session_state.selected_farm_id in task_table['fields'].apply(lambda x: x.get('FarmID')).values:
            # Show the current status of the farm
            st.session_state.selected_task_status = task_table[task_table['fields'].apply(lambda x: x.get('FarmID')) == st.session_state.selected_farm_id]['fields'].apply(lambda x: x.get('Status')).values[0]
            st.write(f"Current Status: {st.session_state.selected_task_status}")
        else:
            responsible_persons = st.multiselect(
                "Choose a responsible person:", 
                employee_table['fields'].apply(lambda x: x.get('Name')), 
                key=f"responsible_person_selectbox_{i}"
            )

            # Add a Note input field
            note = st.text_area("Add a note (optional):", key=f"note_input_{i}")
            # Update the note in the task record
            task_record['Note'] = str(note)

            if st.button("Confirm", key=f"confirm_button_{i}"):
                add_record(TASK_TABLE_ID, task_record)

                # Take Employee ID from the employee_records table where the Name is in responsible_persons
                employee_ids = employee_table[employee_table['fields'].apply(lambda x: x.get('Name') in responsible_persons)]['fields'].apply(lambda x: x.get('EmployeeID')).astype(int).tolist()
                for idx, employee_id in enumerate(employee_ids):
                    employee_task_record = {
                        'UniqueID': idx + len(EMPLOYEE_TASK_TABLE_ID),
                        'TaskID': st.session_state.selected_task_id,
                        'EmployeeID': employee_id
                    }
                    add_record(EMPLOYEE_TASK_TABLE_ID, employee_task_record)
                st.success(f"Row added successfully! {employee_ids}")


def main():
    
    st.set_page_config(layout="wide", page_title="Hotspot Prediction Dashboard")

    sample = pd.read_csv('sample.csv')
    sample['risk'] = np.random.choice([0, 1], size=len(sample))  # for testing purpose
    
    st.markdown(f"""
    <style>
    {custom_css}
    </style>
    """, unsafe_allow_html=True)

    # Main content
    # I want sample['datadate'].iloc[0] which the value is 30-09-2024 to format like 30th September 2024
    latest_update_date = pd.to_datetime(sample['datadate'].iloc[0], format='%d-%m-%Y').strftime('%d %B %Y')

    st.markdown(f"""    
        <h1>🔥 Hotspot Prediction Dashboard</h1>
        <p style='font-size: 18px; color: gray;'>(Latest Update: {latest_update_date})</p>
        """, unsafe_allow_html=True)
    task_table = pd.DataFrame(fetch_records(TASK_TABLE_ID).get('records', []))
    employee_table = pd.DataFrame(fetch_records(EMPLOYEE_TABLE_ID).get('records', []))
    employee_task_table = pd.DataFrame(fetch_records(EMPLOYEE_TASK_TABLE_ID).get('records', []))
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Carbon emission calculations
        st.session_state.total_emission = emission_calculation(sum(sample['Shape_Area']))

        if task_table.empty:
            st.session_state.reduced_emission = 0
        else:
            completed_farms = task_table[task_table['fields'].apply(lambda x: x.get('status') == 'Complete')]
            st.session_state.reduced_emission = emission_calculation(sum(sample[sample['Id'].isin(completed_farms)]['Shape_Area']))

        # Create two columns for the emission metrics
        emission_col1, emission_col2 = st.columns(2)
        
        with emission_col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value" style="color: #ff0000;">{st.session_state.total_emission:,.0f}</div>
                <div class="metric-label">Total Carbon Emission (kg CO2e)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with emission_col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value" style="color: #4dff4d;">{st.session_state.reduced_emission}</div>
                <div class="metric-label">Reduced Carbon Emission (kg CO2e)</div>
            </div>
            """, unsafe_allow_html=True)
        
        selected_province = st.selectbox("🏙️ Choose a province:", ["All Provinces"] + list(THAI_PROVINCES.keys()))
        
        selected_file = st.selectbox(
            "📅 Choose a data file (Year):",
            ["2564", "2565", "2566"]
        )
        selected_file = f"./latlong/{selected_file}.csv"
        
        filtered_data = read_shapefile_data(selected_file)
        
        if selected_province and selected_province != "All Provinces":
            center_lat, center_lon = THAI_PROVINCES[selected_province]
            zoom_start = 10
        else:
            center_lat, center_lon = 13.7563, 100.5018
            zoom_start = 6

        col3, col4 = st.columns([3, 1])
        with col3:
            st.subheader("🗺️ Map of Fire Risk Areas")
        with col4:
            show_risk = st.checkbox("Show Only Fire Risk Areas", value=True)

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
        
        for _, row in filtered_data.iterrows():
            folium.Circle(
                location=[row['LATITUDE'], row['LONGITUDE']],
                radius=500,
                color='red',
                weight=2,
                fill=True,
                fill_color='red',
                fill_opacity=0.1,
            ).add_to(m)
            folium.CircleMarker(
                location=[row['LATITUDE'], row['LONGITUDE']],
                radius=0.5,
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=1,
            ).add_to(m)
        for _, row in sample.iterrows():
                color = 'red' if row['risk'] == 1 else 'green'
                if show_risk and row['risk'] == 0:
                    continue
                folium.Marker(
                    location=[row['lat'], row['long']],
                    icon=folium.Icon(color=color, icon='fire', prefix='fa'),
                    popup=f"Lat: {row['lat']}, Lon: {row['long']}",
                ).add_to(m)
        
        folium_static(m, width=1000, height=600)
        
    with col2:
        st.markdown('<h3 class="dashboard-title">Farms with the Most Recent Burn Dates</h3>', unsafe_allow_html=True)
        # st.markdown('<div class="scrollable-risk-area">', unsafe_allow_html=True)
        if not show_risk:
            st.markdown("""
            <p style='font-size: 18px; color: white; font-weight: bold;'>
            🔴 Previously Burned Areas<br>
            🟢 Never Burned Areas.
            </p>
            """, unsafe_allow_html=True)
        sample = sample.sort_values('predict')

        farms_per_page = 5
        total_farms = len(sample)
        total_pages = (total_farms - 1) // farms_per_page + 1
        
        page = st.selectbox("Page", options=list(range(1, total_pages + 1)))
        
        start_idx = (page - 1) * farms_per_page
        end_idx = min(start_idx + farms_per_page, total_farms)
        
        for i, row in sample.iloc[start_idx:end_idx].iterrows():
            # if show_risk and row['risk'] == 0:
            #     continue
            display_farm_info(i, row, task_table, employee_table, employee_task_table, show_risk)
        
        
        
if __name__ == "__main__":
    main()