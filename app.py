import streamlit as st
import pandas as pd

# Page Setup
st.set_page_config(page_title="PMS Dashboard Ultra Pro", layout="wide")
st.title("🛡️ PMS Dashboard Ultra Pro")

# Direct Data Loading Method
@st.cache_data(ttl=600)
def load_data():
    sheet_id = "1OhVynPQC2-ZbeH47bSOG2vPms_R71M3398Fs1kXSfok"
    sheet_name = "MasterData" 
    
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    df = pd.read_csv(url)
    
    # 1. Amount Cleaning
    if 'Bank Amount' in df.columns:
        df['Bank Amount'] = df['Bank Amount'].astype(str).str.replace(r'[^\d.-]', '', regex=True)
        df['Bank Amount'] = pd.to_numeric(df['Bank Amount'], errors='coerce').fillna(0.0)
        
    # 2. Category Blank Handling
    if 'Category' in df.columns:
        df['Category'] = df['Category'].fillna('BLANK').replace(r'^\s*$', 'BLANK', regex=True)

    # 3. DATE FIX: Text Date ko real Date objects me convert karna (Taki sorting sahi ho)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
        
    return df

with st.spinner("Fetching Master Data..."):
    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ Data load hone me problem aayi. Error: {e}")
        st.stop()

# --- FILTERS ---
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    fy_list = df['FY'].dropna().unique() if 'FY' in df.columns else []
    fy_filter = st.selectbox("FY Select (Only for Pivot)", fy_list)
with col2:
    search_term = st.text_input("Global Search (Txn, Name, Desc)")
with col3:
    cat_list = ["All"] + list(df['Category'].dropna().unique()) if 'Category' in df.columns else ["All"]
    cat_filter = st.selectbox("Category", cat_list)


# --- APPLY FILTERS ---
# Detailed table ke liye Base DF
detailed_df = df.copy()
# Pivot table ke liye Base DF
pivot_source_df = df.copy()

# FY Filter (SIRF Pivot ke liye)
if 'FY' in pivot_source_df.columns:
    pivot_source_df = pivot_source_df[pivot_source_df['FY'] == fy_filter]

# Search Filter (Dono ke liye)
if search_term:
    # Function to search across all columns
    def search_logic(row):
        return row.astype(str).str.contains(search_term, case=False).any()
    detailed_df = detailed_df[detailed_df.apply(search_logic, axis=1)]
    pivot_source_df = pivot_source_df[pivot_source_df.apply(search_logic, axis=1)]

# Category Filter (Dono ke liye)
if cat_filter != "All" and 'Category' in df.columns:
    detailed_df = detailed_df[detailed_df['Category'] == cat_filter]
    pivot_source_df = pivot_source_df[pivot_source_df['Category'] == cat_filter]


# --- PIVOT TABLE ---
st.subheader("📊 Category vs Month Summary")
if not pivot_source_df.empty and 'Category' in df.columns and 'Source' in df.columns and 'Bank Amount' in df.columns:
    try:
        # DUPLICATE TXN FIX: Agar ek hi Txn No ki multiple lines hain, toh unhe hatana
        if 'Txn No.' in pivot_source_df.columns:
            unique_pivot_data = pivot_source_df.drop_duplicates(subset=['Txn No.'])
        else:
            unique_pivot_data = pivot_source_df

        # Creating Pivot
        pivot_df = pd.pivot_table(
            unique_pivot_data, 
            values='Bank Amount', 
            index='Category', 
            columns='Source', 
            aggfunc='sum', 
            fill_value=0
        )
        
        # Month Sequencing
        month_mapping = {
            "apr": 1, "may": 2, "jun": 3, "jul": 4, "aug": 5, "sep": 6, 
            "oct": 7, "nov": 8, "dec": 9, "jan": 10, "feb": 11, "mar": 12
        }
        
        def sort_fy_months(col_name):
            col_str = str(col_name).strip().lower()
            for month_name, order in month_mapping.items():
                if col_str.startswith(month_name):
                    return order
            return 99
            
        sorted_columns = sorted(pivot_df.columns, key=sort_fy_months)
        pivot_df = pivot_df[sorted_columns]
        
        # Grand Total add karna
        pivot_df['Grand Total'] = pivot_df.sum(axis=1)

        # BLANK ROW AT BOTTOM FIX:
        if 'BLANK' in pivot_df.index:
            blank_row = pivot_df.loc['BLANK']
            pivot_df = pivot_df.drop('BLANK')
            pivot_df.loc['BLANK'] = blank_row # Wapas sabse niche add kiya
            
        st.dataframe(pivot_df, use_container_width=True)
    except Exception as e:
        st.warning(f"Pivot table banane mein dikkat aayi: {e}")

# --- DETAILED TRANSACTIONS TABLE ---
st.subheader("📝 Filtered Transactions (All FY Data)")
# Date column config set ki gayi hai taaki wo DD/MM/YYYY format me dikhe aur properly sort ho
st.dataframe(
    detailed_df, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Date": st.column_config.DateColumn("Date", format="DD/MM/YYYY")
    }
)

# Export Data Button
csv = detailed_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="⬇️ Export Detailed Data",
    data=csv,
    file_name='PMS_Export.csv',
    mime='text/csv',
)
