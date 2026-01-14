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
    # API ENDPOINT
    url = "https://webapi.legistar.com/v1/philadelphia/events"
    
    # SAFER QUERY: We let Python handle the encoding of spaces and symbols
    # We ask for the next 100 events to keep it fast
    params = {
        '$filter': f"EventDate ge datetime'{datetime.now().year}-01-01'",
        '$top': 100
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        # ERROR TRAP: Check if the API sent an error dictionary instead of a list
        if isinstance(data, dict):
            # If it's a dictionary, it's likely an error message. Print it for debugging.
            st.warning(f"⚠️ API Notice: {data}")
            return pd.DataFrame()
            
        # If it is a list, we can process it!
        if isinstance(data, list):
            df = pd.DataFrame(data)
            
            if df.empty:
                return pd.DataFrame()

            # Select and Rename the columns we actually care about
            # We use .get() to avoid crashing if a column is missing
            clean_df = pd.DataFrame()
            clean_df["Committee / Body"] = df.get("EventBodyName", "Unknown")
            clean_df["Date"] = df.get("EventDate", "").str.split('T').str[0]
            clean_df["Time"] = df.get("EventTime", "")
            clean_df["Link"] = df.get("EventSiteURL", "#")
            
            # Sort by date
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