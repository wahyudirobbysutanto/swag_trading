import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from db_connector import get_connection

def show_chart_page():
    st.set_page_config(layout="wide")
    st.title("Chart Saham Interaktif ala Stockbit")

    def get_tickers():
        conn = get_connection()
        query = "SELECT DISTINCT ticker FROM SwingScreeningArchive ORDER BY ticker"
        df = pd.read_sql(query, conn)
        conn.close()
        return df['ticker'].tolist()

    tickers = get_tickers()

    selected_ticker = st.selectbox("Pilih Ticker", options=[''] + tickers, index=0)

    if selected_ticker:
        conn = get_connection()
        query = """
            SELECT tanggal, harga, ema8, ema20, ema50, ema200, volume
            FROM SwingScreeningArchive
            WHERE ticker = ?
            ORDER BY tanggal
        """
        df = pd.read_sql(query, conn, params=[selected_ticker])
        conn.close()

        if df.empty:
            st.warning("Data tidak ditemukan untuk ticker ini.")
        else:
            df['tanggal'] = pd.to_datetime(df['tanggal'])

            fig = go.Figure()

            fig.add_trace(go.Scatter(x=df['tanggal'], y=df['harga'], name='Harga', line=dict(color='yellow')))
            fig.add_trace(go.Scatter(x=df['tanggal'], y=df['ema8'], name='EMA8', line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df['tanggal'], y=df['ema20'], name='EMA20', line=dict(color='orange')))
            fig.add_trace(go.Scatter(x=df['tanggal'], y=df['ema50'], name='EMA50', line=dict(color='green')))
            fig.add_trace(go.Scatter(x=df['tanggal'], y=df['ema200'], name='EMA200', line=dict(color='red')))

            fig.add_trace(go.Bar(
                x=df['tanggal'], 
                y=df['volume'], 
                name='Volume',
                marker_color='lightgrey',
                yaxis='y2',
                opacity=0.4
            ))

            fig.update_layout(
                title=f"Chart {selected_ticker} + EMA & Volume",
                xaxis=dict(title='Tanggal', rangeslider_visible=False),
                yaxis=dict(title='Harga'),
                yaxis2=dict(title='Volume', overlaying='y', side='right', showgrid=False),
                hovermode="x unified",
                height=600,
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(t=50, b=50)
            )

            st.plotly_chart(fig, use_container_width=True)
