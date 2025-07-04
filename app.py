
import streamlit as st
from chart_view import show_chart_page
from personal_recommendation import show_personal_page
from history_personal import show_history_personal
from latest_screening import show_latest_screening

st.set_page_config(page_title="Swing Screener", layout="wide")

page = st.sidebar.selectbox("Pilih Halaman", [
    "📋 Data Screening Terakhir",
    "📈 Chart Screening",
    "🧠 Personal Recommendation",
    "History Evaluasi"
])

if page == "📈 Chart Screening":
    show_chart_page()
elif page == "🧠 Personal Recommendation":
    show_personal_page()
elif page == "History Evaluasi":
    show_history_personal()
elif page == "📋 Data Screening Terakhir":
    show_latest_screening()


#streamlit run app.py
