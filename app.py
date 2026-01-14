import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Art of Civic Duty", page_icon="🏛️", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #2c3e50;}
    div[data-testid="stMetricValue"] {font-size: 24px;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Flag_of_Philadelphia%2C_Pennsylvania.svg/320px-Flag_of_Philadelphia%2C_Pennsylvania.svg.png", width=100)
    st.title("Art of Civic Duty")
    st.caption("Live Feed from Legistar API")
    
    focus_mode = st.radio(
        "Select Scope:",
        ["All Activity", "Center City (Broad)", "Society Hill & Old City (Local)"],
        index=0
    )
    
    st.divider()
    st.write("✅ Connected to Legistar v1 API")

# --- KEYWORDS ---
LOCAL_KEYWORDS = ["Society Hill", "Old City", "District 1", "Squilla", "Washington Square", "Head House", "Penn's Landing"]
CENTER_CITY_KEYWORDS = ["Center City", "Market St", "Broad St", "Rittenhouse", "Logan Square", "Chinatown", "City Hall"]

# --- HELPER FUNCTIONS ---
def highlight_rows(row):
    row_text = str(row.values).lower()
    for k in LOCAL_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
    for k in CENTER_CITY_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #d1ecf1; color: #0c5460'] * len(row)
    return [''] * len(row)

@st.cache_data(ttl=300)
def get_api_data():
    # THE SERVICE ENTRANCE: Official Legistar API
    # We ask for events from Philadelphia, happening this year
    current_year = datetime.now().year
    url = f"https://webapi.legistar.com/v1/philadelphia/events?$filter=EventDate+ge+datetime'{current_year}-01-01'"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Turn the raw JSON list into a neat Table
        if data:
            df = pd.DataFrame(data)
            
            # Select and Rename the columns we actually care about
            clean_df = df[[
                'EventBodyName', 
                'EventDate', 
                'EventTime', 
                'EventSiteURL'
            ]].copy()
            
            clean_df.columns = ["Committee / Body", "Date", "Time", "Link"]
            
            # Clean up the Date format (remove the T00:00:00 stuff)
            clean_df['Date'] = clean_df['Date'].str.split('T').str[0]
            
            # Sort by date (newest first? or upcoming?)
            # Let's filter for TODAY onwards
            clean_df['DateObj'] = pd.to_datetime(clean_df['Date'])
            clean_df = clean_df[clean_df['DateObj'] >= pd.Timestamp.now().normalize()]
            clean_df = clean_df.sort_values('DateObj').drop(columns=['DateObj'])
            
            return clean_df
            
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        
    return pd.DataFrame()

# --- MAIN DASHBOARD ---
st.title("🏛️ Philadelphia Governance Dashboard")

# 1. Get Data
df = get_api_data()

# 2. Filter Data
if not df.empty:
    if focus_mode == "Society Hill & Old City (Local)":
        pattern = '|'.join(LOCAL_KEYWORDS)
        # Check Committee Name AND Date (sometimes agenda details are missing in API summary, so we filter broadly)
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
    elif focus_mode == "Center City (Broad)":
        pattern = '|'.join(CENTER_CITY_KEYWORDS + LOCAL_KEYWORDS)
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
    else:
        filtered_df = df

    # 3. Display Data
    if not filtered_df.empty:
        st.write(f"**Found {len(filtered_df)} upcoming events:**")
        st.dataframe(
            filtered_df.style.apply(highlight_rows, axis=1),
            column_config={
                "Link": st.column_config.LinkColumn("View Agenda"),
                "Time": st.column_config.TextColumn("Time", width="small")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No upcoming meetings found matching your keywords.")
        if not df.empty:
            with st.expander("See all upcoming City meetings"):
                st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.warning("Connected to API, but received no data. (City Hall might be quiet today).")

st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.link_button("Legistar Calendar (Official)", "https://phila.legistar.com/Calendar.aspx")
c2.link_button("Zoning Archive", "https://atlas.phila.gov/")
c3.link_button("Historic Commission", "https://www.phila.gov/departments/philadelphia-historical-commission/")