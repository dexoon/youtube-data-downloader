import streamlit as st
from openai import OpenAI
import time


def fetch_models_with_openai_sdk(api_key=None):
    """Fetch models using OpenAI SDK"""
    try:
        # Configure OpenAI client for OpenRouter
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or "sk-or-test-key"  # OpenRouter allows test key for model listing
        )
        
        # Fetch models
        response = client.models.list()
        
        # Extract model IDs
        model_ids = [model.id for model in response.data]
        return sorted(model_ids)
        
    except Exception as e:
        st.sidebar.error(f"OpenAI SDK error: {str(e)[:60]}...")
        return []

def refresh_models():
    """Refresh models using OpenAI SDK"""
    with st.spinner("Refreshing models via OpenAI SDK..."):
        api_key = st.session_state.get('api_key_temp', 'sk-or-test-key')
        models = fetch_models_with_openai_sdk(api_key)
        
        if models:
            st.session_state.openrouter_models = models
            st.session_state.models_last_updated = time.time()
            st.sidebar.success(f"Loaded {len(models)} models!")
        else:
            # Fallback models
            st.session_state.openrouter_models = [
                "mistralai/mistral-7b-instruct",
                "google/gemini-pro",
                "openai/gpt-3.5-turbo",
                "openai/gpt-4"
            ]
            st.sidebar.warning("Using default models")


