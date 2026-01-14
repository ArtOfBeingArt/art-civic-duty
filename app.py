import streamlit as st
import pandas as pd
import requests
import feedparser
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
    row_text = str(row.values).lower()
    for k in LOCAL_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
    for k in CENTER_CITY_KEYWORDS:
        if k.lower() in row_text:
            return ['background-color: #d1ecf1; color: #0c5460'] * len(row)
    return [''] * len(row)

@st.cache_data(ttl=600)
def get_feed_data():
    rss_url = "https://phila.legistar.com/Feed.aspx?Mode=Calendar&Client=Philadelphia"
    
    # 1. Fetch raw data with "Human" headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    }
    
    try:
        response = requests.get(rss_url, headers=headers, verify=False, timeout=15)
        
        # DEBUG: Check if we are blocked
        if response.status_code != 200:
            return pd.DataFrame(), f"Error: City Server responded with Code {response.status_code}"

        # 2. Parse with feedparser (Industrial Strength Parser)
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            return pd.DataFrame(), "Connected, but found no entries in feed."

        # 3. Extract Data
        data = []
        for entry in feed.entries:
            # Title usually contains: "Committee Name - Date - Time"
            title = entry.title
            link = entry.link
            
            # Clean up the text
            clean_name = title
            clean_date = "Check details"
            
            if " - " in title:
                parts = title.split(" - ")
                if len(parts) >= 2:
                    clean_name = parts[0]
                    # Join the rest in case date/time are split
                    clean_date = " - ".join(parts[1:])
            
            data.append({
                "Meeting": clean_name,
                "When": clean_date,
                "Link": link
            })
            
        return pd.DataFrame(data), "OK"
        
    except Exception as e:
        return pd.DataFrame(), f"Crash Error: {str(e)}"

# --- MAIN PAGE ---
st.title("🏛️ Philadelphia Governance Dashboard")

df, status = get_feed_data()

# STATUS INDICATOR (Hidden if working, visible if broken)
if status != "OK":
    st.error(f"⚠️ Connection Status: {status}")
    st.info("If this is a '403' error, the City is blocking the cloud server's IP address.")

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
        
    # DISPLAY TABLE
    st.write(f"**Found {len(filtered_df)} upcoming items:**")
    st.dataframe(
        filtered_df.style.apply(highlight_rows, axis=1),
        column_config={"Link": st.column_config.LinkColumn("Details")},
        use_container_width=True,
        hide_index=True
    )
    
else:
    if status == "OK":
        st.warning("Feed connected but empty (City might have no meetings scheduled).")
    
    # Only show fallback buttons if data is missing
    st.markdown("### 🔗 Direct Access Links")
    c1, c2, c3 = st.columns(3)
    c1.link_button("Official Calendar", "https://phila.legistar.com/Calendar.aspx")
    c2.link_button("Zoning Board", "https://li.phila.gov/zba-appeals-calendar")
    c3.link_button("Historic Commission", "https://www.phila.gov/departments/philadelphia-historical-commission/")