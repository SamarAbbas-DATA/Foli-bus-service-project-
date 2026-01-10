# FOLI Bus Delay Monitor (Airflow + Postgres + Streamlit)

This project pulls real-time bus operation data from the **FOLI Service Public API**, polls it every 3 minutes using Apache Airflow, transforms/cleans it, and stores it in a local PostgreSQL database.  
A Streamlit app (`dashboard.py`) then reads from Postgres to visualize delays, trends, stops, and status insights.

---

## What the Dashboard Shows

### 1) Delay (seconds) by Bus Number + Bus Name (Line Graph)
- Line chart of **DelaySecs** grouped by **BusNo + BusName**.
- Because a **BusName + LineRef** can appear multiple times, we plot the **average DelaySecs** for clean trend lines.
- Helps spot which buses are consistently running behind.
[alt text](image.png)

---

### 2) Late Lines by Date + Weekly Delays + Raw Sorted Table
- **Bar chart by selected date**: shows **which line(s)** were late on that date.
- **Weekly bar chart (last 7 days)**: DelaySecs trend across the past week for the selected date range.
- Includes a **raw table sorted by DelaySecs** so you can quickly find the worst offenders.

![alt text](image-1.png)


![alt text](image-2.png)
![alt text](image-3.png)

