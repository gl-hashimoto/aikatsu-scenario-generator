import streamlit as st

st.title("Test App")
st.write("If you can see this, Streamlit is working!")

# Test imports
try:
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
    from pages.article_analysis import render_article_analysis_page
    st.success("✅ article_analysis imported")
except Exception as e:
    st.error(f"❌ article_analysis import failed: {e}")

st.write("Test completed!")
