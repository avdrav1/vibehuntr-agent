"""Custom styling for Vibehuntr playground."""

VIBEHUNTR_STYLE = """
<style>
    /* Import Lexend font family (Vibehuntr brand font) */
    @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Lexend', sans-serif !important;
    }
    
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #0F0F1E 0%, #1A1A2E 100%);
    }
    
    /* Header styling */
    header {
        background: rgba(26, 26, 46, 0.8) !important;
        backdrop-filter: blur(10px);
    }
    
    /* Chat messages */
    .stChatMessage {
        background: rgba(26, 26, 46, 0.6) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 107, 107, 0.1) !important;
        padding: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    /* User message */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, rgba(255, 107, 107, 0.2), rgba(255, 107, 107, 0.1)) !important;
        border: 1px solid rgba(255, 107, 107, 0.3) !important;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid="assistant-message"] {
        background: rgba(26, 26, 46, 0.8) !important;
    }
    
    /* Input box */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(26, 26, 46, 0.8) !important;
        border: 2px solid rgba(255, 107, 107, 0.3) !important;
        border-radius: 12px !important;
        color: white !important;
        font-size: 16px !important;
        padding: 12px !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #FF6B6B !important;
        box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.2) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4) !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1A1A2E 0%, #0F0F1E 100%) !important;
        border-right: 1px solid rgba(255, 107, 107, 0.1) !important;
    }
    
    /* Hide sidebar collapse button completely */
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Nuclear option: hide ALL text that looks like icon names */
    *:contains("keyboard_double_arrow_right") {
        display: none !important;
    }
    
    /* Hide any button in header that might show icon text */
    button[kind="header"],
    button[kind="header"] *,
    [data-testid="baseButton-header"],
    [data-testid="baseButton-header"] * {
        font-size: 0 !important;
        color: transparent !important;
    }
    
    /* Completely hide the sidebar toggle */
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapse"] {
        display: none !important;
    }
    
    /* Sidebar widgets */
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stMultiSelect {
        background: rgba(26, 26, 46, 0.6) !important;
        border-radius: 12px !important;
    }
    
    /* Cards and containers */
    .element-container {
        background: transparent !important;
    }
    
    /* Expander - completely reset to fix overlay */
    .streamlit-expanderHeader {
        background: rgba(26, 26, 46, 0.6) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 107, 107, 0.2) !important;
        color: white !important;
        font-weight: 500 !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 107, 107, 0.1) !important;
        border-color: rgba(255, 107, 107, 0.4) !important;
    }
    
    /* Fix text overlay - hide duplicate elements */
    .streamlit-expanderHeader p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.5 !important;
    }
    
    .streamlit-expanderHeader svg {
        flex-shrink: 0 !important;
        margin-right: 8px !important;
    }
    
    /* Force single line display */
    .streamlit-expanderHeader label {
        display: inline !important;
        white-space: nowrap !important;
    }
    
    /* Hide any pseudo-elements that might cause overlay */
    .streamlit-expanderHeader::before,
    .streamlit-expanderHeader::after {
        display: none !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: rgba(15, 15, 30, 0.8) !important;
        border: 1px solid rgba(255, 107, 107, 0.2) !important;
        border-radius: 12px !important;
    }
    
    /* Links */
    a {
        color: #FF6B6B !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    
    a:hover {
        color: #FF8E8E !important;
        text-decoration: underline !important;
    }
    
    /* Success/Info/Warning boxes */
    .stSuccess {
        background: rgba(76, 175, 80, 0.1) !important;
        border-left: 4px solid #4CAF50 !important;
        border-radius: 8px !important;
    }
    
    .stInfo {
        background: rgba(33, 150, 243, 0.1) !important;
        border-left: 4px solid #2196F3 !important;
        border-radius: 8px !important;
    }
    
    .stWarning {
        background: rgba(255, 152, 0, 0.1) !important;
        border-left: 4px solid #FF9800 !important;
        border-radius: 8px !important;
    }
    
    .stError {
        background: rgba(244, 67, 54, 0.1) !important;
        border-left: 4px solid #F44336 !important;
        border-radius: 8px !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 15, 30, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #FF6B6B;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-top-color: #FF6B6B !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(26, 26, 46, 0.6);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.7);
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E) !important;
        color: white !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #FF6B6B !important;
        font-weight: 700 !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: white !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }
    
    h1 {
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Vibehuntr logo/branding */
    .vibehuntr-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .vibehuntr-logo {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF6B6B, #FF8E8E, #FFB6B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.03em;
        margin-bottom: 0.5rem;
    }
    
    .vibehuntr-tagline {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Glassmorphism effect for cards */
    .glass-card {
        background: rgba(26, 26, 46, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 107, 107, 0.1) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }
</style>
"""

VIBEHUNTR_HEADER = """
<div class="vibehuntr-header">
    <div class="vibehuntr-logo">🎉 Vibehuntr</div>
    <div class="vibehuntr-tagline">Discover. Plan. Vibe.</div>
</div>
"""
