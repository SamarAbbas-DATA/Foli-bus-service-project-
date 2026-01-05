import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime, timedelta
#
st.set_page_config(page_title="Föli Bus Analytics", page_icon="🚨",  layout="wide")
# Custom CSS    
st.markdown("""
    <style>
        .stApp {
            background-color: #00172B; /* Deep Navy Blue */
        }
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
        }
        [data-testid="stSidebar"] {
            background-color: #002B49; /* Slightly lighter blue for sidebar */
        }
        h1, h2, h3, p, span {
            color: #E0E0E0 !important; /* Off-white text for readability */
        }
    </style>
""", unsafe_allow_html=True)

# DATABASE CONNECTIONS
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        user="postgres", password = "yam%40110%23%23", host="localhost", port="5432", database="new_db"
    )

@st.cache_data
def get_bus_data():
    conn = init_connection()
    query = """
    SELECT service_date, lineref, bus_name, next_stop, 
           AVG(delaysecs) as delaysecs, 
           MAX(inpanic::int) as inpanic, 
           MAX(incongestion::int) as incongestion 
    FROM vehicles
    GROUP BY service_date, lineref, bus_name, next_stop
    """
    df = pd.read_sql(query, conn)
    df["service_date"] = pd.to_datetime(df["service_date"]).dt.date
    df["lineref"] = df["lineref"].astype(str)
    return df

df_base = get_bus_data()

# --- HEADER SECTION (Centered Logo & Title) ---
t1, t2 = st.columns([1,2] , vertical_alignment="center")
with t1:
    st.image("images.png", caption="Föli Service", width=200)
    # st.markdown("<h1 style='text-align: center;'>Föli Bus Analysis</h1>", unsafe_allow_html=True)
with t2:
    st.title(" ")
    st.title("Föli Bus Analysis")

#  UNIQUE TRIP ANALYSIS (LEFT DESC | RIGHT GRAPH) ---
# Logic for Unique Trips
col1, col2 = st.columns([1, 2])

# --- LOGIC FOR SECTION 1 ---
df_trips = df_base.copy()
df_trips['trip_id'] = df_trips['bus_name'] + " (Line: " + df_trips['lineref'] + ")"

# Group to ensure only ONE point per date for the graph
df_plot = df_trips.groupby(['service_date', 'trip_id'])['delaysecs'].mean().reset_index()

with col1:
    st.text("Compact dashboard using the bus Föli public API to track delay seconds by bus and stop in real time. It also visualizes traffic congestion and flags panic or disruption signals")
    st.write("Select a specific Bus-Line combination to track history.")
    unit_choice = st.selectbox("Search Bus + Line:", options=sorted(df_plot["trip_id"].unique()))

with col2:
    # Filter and sort by date for a proper time-series line
    s1_data = df_plot[df_plot["trip_id"] == unit_choice].sort_values("service_date")
    
    fig1 = px.line(s1_data, x="service_date", y="delaysecs", 
                  title=f"Performance Trend: {unit_choice}",
                  markers=True, line_shape="spline",
                  labels={"service_date": "Date", "delaysecs": "Avg Delay (s)"})
    
    fig1.update_traces(line_color="#AD0404") 
    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", 
                      plot_bgcolor="rgba(0,0,0,0)",
                      font_color="white")
    st.plotly_chart(fig1, use_container_width=True)

# VARIABLE DATE & WEEKLY TOP DELAYS
st.markdown("---")
col_today, col_week = st.columns(2)

with col_today:
    st.subheader(" Top Delays by Date")
    target_date = st.date_input("Select Date for Analysis:", value=df_base["service_date"].max())
    
    df_selected_day = df_base[df_base["service_date"] == target_date]
    if not df_selected_day.empty:
        top_day = df_selected_day.groupby("lineref")["delaysecs"].mean().sort_values(ascending=False).head(10).reset_index()
        fig2 = px.bar(top_day, x="lineref", y="delaysecs", color="delaysecs",
                     title=f"Highest Delays on {target_date}", color_continuous_scale="OrRd")
        fig2.update_xaxes(type='category') 
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No data found for this date.")

with col_week:
    st.subheader(" Top Delays Last 7 Days")
    st.subheader("  ")

    last_week_date = df_base["service_date"].max() - timedelta(days=7)
    df_week = df_base[df_base["service_date"] >= last_week_date]
    top_week = df_week.groupby("lineref")["delaysecs"].mean().sort_values(ascending=False).head(15).reset_index()
     
    fig3 = px.bar(top_week, x="lineref", y="delaysecs", color="delaysecs",
                 title="Weekly Avg Delay Leaders", color_continuous_scale="sunsetdark")
    fig3.update_xaxes(type='category')
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

st.dataframe(df_selected_day.sort_values(by = 'delaysecs', ascending=False))

#  ALL LINE REFS GENERAL ALL TIME 
st.markdown("---")
st.subheader(" Historical Comparison: All Line References")
all_time_trend = df_base.groupby(["service_date", "lineref"])["delaysecs"].mean().reset_index()
fig4 = px.line(all_time_trend, x="service_date", y="delaysecs", color="lineref",
              title="Global Delay Comparison (All Lines)")
fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig4, use_container_width=True)


# TOP STOPS BY DATE & INCIDENTS
st.markdown("---")
col_stops, col_incidents = st.columns([2, 1])

with col_stops:
    st.subheader(" Top Stop Delays")
    stop_date = st.date_input("Select Date for Stop Analysis:", value=df_base["service_date"].max())
    df_stop_date = df_base[df_base["service_date"] == stop_date]
    
    if not df_stop_date.empty:
        top_stops = df_stop_date.groupby("next_stop")["delaysecs"].mean().sort_values(ascending=False).head(15).reset_index()
        fig5 = px.bar(top_stops, x="next_stop", y="delaysecs", 
                     color="delaysecs", color_continuous_scale='Reds',
                     title=f"Worst Performing Stops on {stop_date}",
                     labels={"next_stop": "Stop Name", "delaysecs": "Avg Delay (sec)"}) 
        fig5.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.warning("No stop data for this date.")

with col_incidents:
    st.subheader(f" top stops for date {stop_date}")
    st.subheader(' ')
    st.dataframe(top_stops[["next_stop", "delaysecs"]], use_container_width=True)
    
st.subheader(" Panic & Congestion Monitor")
panic_count = df_base[df_base["inpanic"] > 0].shape[0]
cong_count = df_base[df_base["incongestion"] > 0].shape[0]

st.metric("Total Panic Events", panic_count)
st.metric("Total Congestion Events", cong_count)
    
st.write("**Recent Critical Incidents (lastest updated)**")
incident_logs = df_base[(df_base["inpanic"] > 0) | (df_base["incongestion"] > 0)].tail(10)
st.dataframe(incident_logs[["service_date", "lineref", "bus_name", "inpanic", "incongestion"]], use_container_width=True)