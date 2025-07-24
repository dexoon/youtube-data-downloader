from datetime import datetime
import time
import streamlit as st
import logging
from googleapiclient.discovery import build
from openrouter import refresh_models
from youtube import get_channel_id, get_last_video_ids, get_uploads_playlist_id, get_video_descriptions
from data_processing import process_video_descriptions
from io import BytesIO
import pandas as pd
import dotenv
import os

# Load environment variables from .env file
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='app.log',
                    filemode='a')

st.set_page_config(layout="wide")

st.title("YouTube Video Link Extractor")

CHANNEL_LINK = st.text_input("Enter YouTube Channel URL", "https://www.youtube.com/@denis_chuzhoy/videos",
                             key="channel_link",
                            help="Enter the full URL of the YouTube channel you want to analyze.")
NUM_VIDEOS = st.slider("Number of recent videos to analyze", 1, 50, 10)

st.sidebar.header("YouTube API Configuration")
YOUTUBE_API_KEY = st.sidebar.text_input(
    "YouTube API Key", 
    type="password",
    key="youtube_api_key",
    help="Get your key from https://console.developers.google.com/apis/credentials"
) or st.secrets.get("YOUTUBE_API_KEY", "")
st.sidebar.header("OpenRouter Configuration")
OPENROUTER_API_KEY = st.sidebar.text_input(
    "OpenRouter API Key",
    type="password", 
    key="openrouter_api_key",
    help="Get your key from https://openrouter.ai/keys"
) or st.secrets.get("OPENROUTER_API_KEY", "")
# Model selection section
st.sidebar.subheader("Model Selection")

# Refresh controls
col1, col2 = st.sidebar.columns([2, 1])
with col1:
    if st.button("🔄 Refresh Models", key="refresh_btn"):
        refresh_models()
with col2:
    if st.button("❓", key="help_btn", help="Fetch latest models from OpenRouter"):
        st.info("This fetches the most up-to-date list of available models from OpenRouter")

# Load models on first run
if 'openrouter_models' not in st.session_state or not st.session_state.openrouter_models:
    refresh_models()

# Model selection dropdown
OPENROUTER_MODEL = st.sidebar.selectbox(
    "Select Model",
    options=st.session_state.openrouter_models,
    index=0 if st.session_state.openrouter_models else None,
    key="model_selector"
)

# Model info and stats
if st.session_state.models_last_updated:
    minutes_ago = int((time.time() - st.session_state.models_last_updated) / 60)
    st.sidebar.caption(f"Updated {minutes_ago}m ago • {len(st.session_state.openrouter_models)} models")

if st.button("Analyze Videos"):
    st.session_state.pop("df", None)
    st.session_state.pop("excel_data", None)
    logging.info("'Analyze Videos' button clicked.")
    if not YOUTUBE_API_KEY:
        st.error("Please enter your YouTube API Key.")
        logging.warning("API Key was not provided.")
    else:
        try:
            with st.spinner("Fetching data from YouTube..."):
                logging.info("Starting video analysis.")
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                channel_id = get_channel_id(CHANNEL_LINK, YOUTUBE_API_KEY)
                playlist_id = get_uploads_playlist_id(youtube, channel_id)
                video_ids = get_last_video_ids(youtube, playlist_id, max_results=NUM_VIDEOS)
                descriptions = get_video_descriptions(youtube, video_ids)
                df = process_video_descriptions(descriptions, openrouter_api_key=OPENROUTER_API_KEY, openrouter_model=OPENROUTER_MODEL)

                if df is not None and not df.empty:
                    st.session_state["df"] = df
                    logging.info(f"Found {len(df)} videos with links.")

                    # Convert dataframe to Excel file
                    
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False)
                        writer.close()
                    
                    st.session_state["excel_data"] = buffer.getvalue()
                    
                else:
                    st.info("No links found in the recent videos.")
                    logging.info("No links found in the analyzed videos.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            logging.error(f"An error occurred during analysis: {e}", exc_info=True)
if "df" in st.session_state and "excel_data" in st.session_state:
    st.dataframe(st.session_state["df"])
    st.download_button(
        label="Download data as Excel",
        data=st.session_state["excel_data"],
        file_name=f'{CHANNEL_LINK}_{datetime.now().strftime("%Y-%m-%d") }.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )