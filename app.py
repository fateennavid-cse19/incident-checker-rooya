import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import urllib.parse

load_dotenv()

def get_connection():
    user = os.getenv('DB_USER')
    password = urllib.parse.quote_plus(os.getenv('DB_PASSWORD'))
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    db = os.getenv('DB_NAME')
    conn_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return create_engine(conn_url)

def load_sql_query(file_path):
    with open(file_path,'r') as f:
        return f.read()

# --- Page Configuration ---
st.set_page_config(page_title="Incident Dashboard", layout="wide")

# Custom CSS for the "Pill" metrics
st.markdown("""
    <style>
    .metric-container {
        text-align: center;
    }
    .metric-label {
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 12px;
        color: var(--text-color);
    }
    .metric-pill {
        background-color: #F5ECE1; /* Light beige/cream background */
        border-radius: 50px;
        padding: 12px 35px;
        display: inline-block;
        color: #1E1E1E; /* Dark text for contrast */
        font-size: 32px;
        font-weight: 800;
        min-width: 150px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
    }
    /* Style for the Leaderboard Table */
    .stDataFrame { border: 1px solid #3d3d3d; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("Dashcam Trip Incident Review")

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Filters")
    
    # 1. Define Timeframe options
    timeframe_options = {
        "1 Hour": "1 hour",
        "24 Hours": "24 hours",
        "7 Days": "7 days",
        "30 Days": "30 days",
        "90 Days": "90 days"
    }
    
    # 2. Add the Toggle (Selectbox or Pills)
    selected_label = st.selectbox("Select Timeframe", options=list(timeframe_options.keys()), index=1)
    db_interval = timeframe_options[selected_label]
    
    st.divider()
    if st.button('🔄 Refresh Data'):
        st.rerun()

try:
    sql_query = load_sql_query('review-check.sql')
    engine = get_connection()
    with st.spinner(f'Fetching incident data for the last {selected_label}...'):
        with engine.connect() as conn:
            full_df = pd.read_sql(
                text(sql_query), 
                conn, 
                params={"time_window": db_interval}
            )

    if not full_df.empty:

        summary_df = full_df[full_df['report_type'] == 'summary']
        leaderboard_df = full_df[full_df['report_type'] == 'leaderboard'].sort_values('count', ascending=False)
        
        # Prepare Data
        # Extract counts based on the 'incident_check' labels
        reviewed_count = summary_df[summary_df['label'] == 'reviewed']['count'].sum()
        needs_review_count = summary_df[summary_df['label'] == 'needs-review']['count'].sum()

        # Ensure they are integers
        reviewed_count = int(reviewed_count) if not pd.isna(reviewed_count) else 0
        needs_review_count = int(needs_review_count) if not pd.isna(needs_review_count) else 0
        total_incidents = int(reviewed_count + needs_review_count)

        # 2. Layout: Metric (Left) | Donut Chart (Center) | Metric (Right)
        # vertical_alignment="center" keeps the pills level with the middle of the circle
        col_left, col_chart, col_right = st.columns([1, 2, 1], vertical_alignment="center")

        with col_left:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Reviewed</div>
                    <div class="metric-pill">{reviewed_count:,}</div>
                </div>
            """, unsafe_allow_html=True)

        with col_chart:
            fig = px.pie(
                summary_df, 
                values='count', 
                names='label', 
                hole=0.75, # Thinner ring for a cleaner look
                color='label',
                color_discrete_map={'needs-review':'#EF553B', 'reviewed':'#00CC96'}
            )

            fig.update_layout(
                annotations=[{
                    "text": f"Total<br><b>{total_incidents:,}</b>",
                    "x": 0.5, "y": 0.5, 
                    "font_size": 26, 
                    "showarrow": False,
                    "font_color": "#808495"
                }],
                showlegend=False,
                margin=dict(t=20, b=20, l=20, r=20),
                height=450
            )

            fig.update_traces(
                textinfo='none', # Hide percentages on the slices
                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>"
            )
            
            st.plotly_chart(fig, width='stretch')

        with col_right:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-label">Need to review</div>
                    <div class="metric-pill">{needs_review_count:,}</div>
                </div>
            """, unsafe_allow_html=True)
        
        # 3. Leaderboard Table
        st.divider()
        st.subheader("Annotator Leaderboard")

        if not leaderboard_df.empty:
            # Displaying a clean table
            display_ldb = leaderboard_df[['annotator', 'count']].rename(columns={'annotator': 'Annotator Name', 'count': 'Incidents Reviewed'})
            
            # Using st.columns to center the table or put a chart next to it
            l_col, r_col = st.columns([2, 1])
            with l_col:
                st.dataframe(display_ldb, width='stretch', hide_index=True)
            with r_col:
                # Small Bar Chart for visual comparison
                bar_fig = px.bar(display_ldb, x='Incidents Reviewed', y='Annotator Name', orientation='h',
                                 color_discrete_sequence=['#00CC96'])
                bar_fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0), yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(bar_fig, width='stretch')
        else:
            st.info("No reviews recorded by annotators in this timeframe.")

    else:
        st.info("✨ No incidents found in the last 24 hours.")

except FileNotFoundError:
    st.error("Error: 'review-check.sql' file not found in the directory.")
except Exception as e:
    st.error(f"Error: {e}")