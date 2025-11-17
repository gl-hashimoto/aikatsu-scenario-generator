import streamlit as st
import sys
import os

# ページ設定を最初に呼び出す
st.set_page_config(page_title="Test App", page_icon="🧪")

st.title("Test App")
st.write("If you can see this, Streamlit is working!")

# パス確認
st.write(f"Current directory: {os.getcwd()}")
st.write(f"__file__: {__file__}")
st.write(f"sys.path: {sys.path[:3]}")

# Test imports
try:
    sys.path.append(os.path.dirname(__file__))
    from utils.prompt_library import PromptLibrary
    st.success("✅ PromptLibrary imported")
except Exception as e:
    st.error(f"❌ PromptLibrary import failed: {e}")

try:
    from utils.scenario_manager import load_scenario_history
    st.success("✅ scenario_manager imported")
except Exception as e:
    st.error(f"❌ scenario_manager import failed: {e}")

try:
    from modules.article_analysis import render_article_analysis_page
    st.success("✅ article_analysis imported")
except Exception as e:
    st.error(f"❌ article_analysis import failed: {e}")

st.write("Test completed!")
