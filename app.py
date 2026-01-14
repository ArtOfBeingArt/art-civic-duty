import streamlit as st
import pandas as pd
import requests
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Art of Civic Duty", page_icon="🏛️", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #2c3e50;}
    .stDataFrame {font-size: 16px;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Flag_of_Philadelphia%2C_Pennsylvania.svg/320px-Flag_of_Philadelphia%2C_Pennsylvania.svg.png", width=100)
    st.title("Art of Civic Duty")
    st.header("⚡ Quick Focus")
    focus_mode = st.radio(
        "Select Scope:",
        ["All Activity", "Center City (Broad)", "Society Hill & Old City (Local)"],
        index=0
    )
    st.divider()

# --- KEYWORDS ---
LOCAL_KEYWORDS = ["Society Hill", "Old City", "Squilla", "Washington Square", "Head House", "Penn's Landing", "Spruce St", "Pine St"]
CENTER_CITY_KEYWORDS = ["Center City", "Market St", "Broad St", "Rittenhouse", "Logan Square", "Chinatown", "City Hall", "Vine St"]
ALL_KEYWORDS = LOCAL_KEYWORDS + CENTER_CITY_KEYWORDS

# --- HELPER FUNCTIONS ---
def highlight_rows(row):
    # Convert row to text safely
    row_text = str(row.values).lower()
    for k in LOCAL_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
    for k in CENTER_CITY_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #d1ecf1; color: #0c5460'] * len(row)
    return [''] * len(row)

@st.cache_data(ttl=600)
def get_schedule():
    url = "https://phila.legistar.com/Calendar.aspx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        
        # THE SNIPER SCOPE: match="Meeting Time"
        # This tells pandas: "Only bring me tables that contain this specific text."
        # This ignores the search bars and headers.
        dfs = pd.read_html(response.content, match="Meeting Time")
        
        if len(dfs) > 0:
            df = dfs[0]
            
            # Clean up: Legistar tables often have a weird first column or empty rows
            # 1. Drop columns that are all NaN (empty)
            df = df.dropna(axis=1, how='all')
            
            # 2. Rename columns safely if they exist
            # We just return the raw table first to ensure it works
            return df, "OK"
            
    except Exception as e:
        return pd.DataFrame(), str(e)
        
    return pd.DataFrame(), "No Data Found"

# --- DASHBOARD ---
st.title("🏛️ Philadelphia Governance Dashboard")

df, status = get_schedule()

if not df.empty:
    # FILTERS
    if focus_mode == "Society Hill & Old City (Local)":
        pattern = '|'.join(LOCAL_KEYWORDS)
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
    elif focus_mode == "Center City (Broad)":
        pattern = '|'.join(ALL_KEYWORDS)
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
    else:
        filtered_df = df
        
    st.write(f"**Upcoming Schedule:**")
    st.dataframe(
        filtered_df.style.apply(highlight_rows, axis=1),
        use_container_width=True,
        hide_index=True
    )
else:
    # Error Handling
    st.error(f"⚠️ Connection Status: {status}")
    st.info("The City website might be blocking the scraper or the layout changed.")
    
    st.markdown("### 🔗 Direct Access Links")
    c1, c2, c3 = st.columns(3)
    c1.link_button("Official Calendar", "https://phila.legistar.com/Calendar.aspx")
    c2.link_button("Zoning Board", "https://li.phila.gov/zba-appeals-calendar")
    c3.link_button("Historic Commission", "https://www.phila.gov/departments/philadelphia-historical-commission/")