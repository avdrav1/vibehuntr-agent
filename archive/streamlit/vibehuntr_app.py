"""Vibehuntr-branded app wrapper for ADK playground."""

from google.adk.apps.app import App
from app.agent import root_agent
from app.playground_style import VIBEHUNTR_STYLE, VIBEHUNTR_HEADER

# Create the app with custom branding
app = App(
    root_agent=root_agent,
    name="vibehuntr",
    description="Your AI-powered event planning assistant. Find venues, plan events, and coordinate with friends!",
)

# Add custom styling (this will be injected by Streamlit)
app.custom_css = VIBEHUNTR_STYLE
app.custom_header = VIBEHUNTR_HEADER
