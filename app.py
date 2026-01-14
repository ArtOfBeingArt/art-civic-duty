import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import urllib3

# Suppress SSL warnings (The City's security certificate is often old)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Art of Civic Duty", page_icon="🏛️", layout="wide")

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #2c3e50;}
    .stDataFrame {font-size: 16px;}
    div[data-testid="stMetricValue"] {font-size: 24px;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Flag_of_Philadelphia%2C_Pennsylvania.svg/320px-Flag_of_Philadelphia%2C_Pennsylvania.svg.png", width=100)
    st.title("Art of Civic Duty")
    st.caption("Monitoring Philadelphia Governance")
    
    st.header("⚡ Quick Focus")
    focus_mode = st.radio(
        "Select Scope:",
        ["All Activity", "Center City (Broad)", "Society Hill & Old City (Local)"],
        index=0
    )
    
    st.divider()
    st.write("📡 Connection Status: Monitoring")

# --- KEYWORDS ---
LOCAL_KEYWORDS = ["Society Hill", "Old City", "District 1", "Squilla", "Washington Square", "Head House", "Penn's Landing", "Spruce St", "Pine St"]
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
def get_council_feed():
    # RSS URL: The public broadcast feed
    rss_url = "https://phila.legistar.com/Feed.aspx?Mode=Calendar&Client=Philadelphia"
    
    try:
        # STEALTH HEADERS: Vital to get past the firewall
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # Request with 10 second timeout
        response = requests.get(rss_url, headers=headers, verify=False, timeout=10)
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        meetings = []
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else "Unknown"
            link = item.find('link').text if item.find('link') is not None else "#"
            
            # Attempt to split Date from Title (Format: "Committee Name - 1/20/2026 - 10:00 AM")
            date_str = "See Link"
            meeting_name = title
            
            if " - " in title:
                parts = title.split(" - ")
                # Usually the last two parts are Date and Time, the first part is Name
                if len(parts) >= 2:
                    meeting_name = parts[0]
                    date_str = parts[1]
            
            meetings.append({
                "Meeting Name": meeting_name,
                "Date": date_str,
                "Link": link
            })
            
        if meetings:
            return pd.DataFrame(meetings), "Online"
            
    except Exception as e:
        # If this fails, we return empty so the app doesn't crash
        pass
        
    return pd.DataFrame(), "Offline"

# --- DASHBOARD ---
st.title("🏛️ Philadelphia Governance Dashboard")

# 1. Get Data
df, status = get_council_feed()

if status == "Offline":
    st.warning("⚠️ Live Feed Temporarily Unavailable (City Firewall Active).")
    st.info("Use the direct links below to check schedules manually.")
else:
    if focus_mode == "Society Hill & Old City (Local)":
        st.info(f"🔎 Focused Mode: Showing only updates for **{focus_mode}**.")

# 2. Display Tabs
tab1, tab2, tab3 = st.tabs(["📜 City Council Schedule", "🏗️ Zoning (ZBA)", "🧱 Historic Preservation"])

with tab1:
    if not df.empty:
        # Apply Filters
        if focus_mode == "Society Hill & Old City (Local)":
            pattern = '|'.join(LOCAL_KEYWORDS)
            filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
        elif focus_mode == "Center City (Broad)":
            pattern = '|'.join(ALL_KEYWORDS)
            filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(pattern, case=False)).any(axis=1)]
        else:
            filtered_df = df
            
        if not filtered_df.empty:
            st.dataframe(
                filtered_df.style.apply(highlight_rows, axis=1), 
                column_config={"Link": st.column_config.LinkColumn("Meeting Details")},
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.write("No meetings found matching your keywords right now.")
            with st.expander("View All Upcoming Meetings"):
                st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Graceful Fallback if data is empty (Offline)
        st.link_button("📅 Open Official City Council Calendar", "https://phila.legistar.com/Calendar.aspx")

with tab2:
    st.header("Zoning Watch")
    c1, c2 = st.columns(2)
    c1.link_button("Check Society Hill Zoning", "https://atlas.phila.gov/")
    c2.link_button("ZBA Calendar", "https://li.phila.gov/zba-appeals-calendar")

with tab3:
    st.header("Historic Preservation")
    st.link_button("Historical Commission Agenda", "https://www.phila.gov/departments/philadelphia-historical-commission/public-meetings/")