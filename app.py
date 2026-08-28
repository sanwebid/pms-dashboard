import streamlit as st
import pandas as pd

# Page Setup
st.set_page_config(page_title="PMS Dashboard Ultra Pro", layout="wide")
st.title("🛡️ PMS Dashboard Ultra Pro")

# Direct Data Loading Method (No extra connection library needed)
@st.cache_data(ttl=600)
def load_data():
    sheet_id = "1OhVynPQC2-ZbeH47bSOG2vPms_R71M3398Fs1kXSfok"
    
    # AGAR AAPKI SHEET KE NAAM ME SPACE HAI TOH ISE "Master Data" KAR DEIN
    sheet_name = "MasterData" 
    
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    return df

with st.spinner("Fetching Master Data..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Data load hone me problem aayi. Check karein ki Google Sheet me niche tab ka naam exact 'MasterData' hi hai na? Error: {e}")
        st.stop()

# --- FILTERS ---
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    fy_list = df['FY'].dropna().unique() if 'FY' in df.columns else []
    fy_filter = st.selectbox("FY Select", fy_list)
with col2:
    search_term = st.text_input("Global Search (Txn, Name, Desc)")
with col3:
    cat_list = ["All"] + list(df['Category'].dropna().unique()) if 'Category' in df.columns else ["All"]
    cat_filter = st.selectbox("Category", cat_list)

# Apply Filters
if 'FY' in df.columns:
    filtered_df = df[df['FY'] == fy_filter]
else:
    filtered_df = df

if search_term:
    filtered_df = filtered_df[filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
if cat_filter != "All" and 'Category' in df.columns:
    filtered_df = filtered_df[filtered_df['Category'] == cat_filter]

# --- PIVOT TABLE ---
st.subheader("📊 Category vs Month Summary")
if not filtered_df.empty and 'Category' in df.columns and 'Date' in df.columns and 'Bank Amount' in df.columns:
    pivot_df = pd.pivot_table(
        filtered_df, 
        values='Bank Amount', 
        index='Category', 
        columns='Date', 
        aggfunc='sum', 
        fill_value=0
    )
    st.dataframe(pivot_df, use_container_width=True)

# --- DETAILED TRANSACTIONS TABLE ---
st.subheader("📝 Filtered Transactions")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# Export Data Button
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Export Data",
    data=csv,
    file_name='PMS_Export.csv',
    mime='text/csv',
)
