import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
    /* Import Premium Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@500;700&display=swap');

    /* Main Background Gradient */
    .stApp {
        background: linear-gradient(741deg, #f7fafc 0%, #e4e8f0 100%);
        font-family: 'Inter', sans-serif;
    }

    /* Title Header with Glowing Gradient */
    .header-text {
        font-family: 'Poppins', sans-serif;
        font-size: 3rem !important;
        font-weight: 700;
        background: linear-gradient(90deg, #1e40af, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }

    /* Content Card (Used for Summaries) */
    /* Update this section in styles.py */
    .content-card {
        background: #ffffff; 
        padding: 25px; 
        border-radius: 15px;
        border-left: 6px solid #2563eb;
        color: #1e293b; 
        line-height: 1.5;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }

    /* Make Bold Headers pop */
    .content-card b {
        color: #1e3a8a; /* Deep blue for headers */
        font-weight: 700;
        display: inline-block;
        margin-top: 10px;
        text-transform: uppercase;
        font-size: 0.95rem;
    }

    /* Tighten the gap if a bold header follows a line break */
    .content-card br + b {
        margin-top: 15px;
    }

    /* TIGHTER PARAGRAPHS */
    .content-card p {
        margin-bottom: 10px !important;
    }

    /* NORMAL LIST SPACING (Not too wide) */
    .content-card li {
        margin-bottom: 5px !important;
        margin-top: 0px !important;
    }

    .content-card ul, .content-card ol {
        margin-top: 5px !important;
        margin-bottom: 10px !important;
        padding-left: 25px !important;
    }

    /* FIXES THE "EMPTY BOX" GLITCH */
    .content-card:empty {
        display: none;
    }
                            
    /* --- SIDEBAR BLOG CARDS (NEW) --- */
            
    a {
        text-decoration: none !important;
    }
                    
    .sidebar-card {
        background: white;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 12px;
        border-left: 5px solid #2563eb; /* Blue accent */
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: block;
    }

    .sidebar-card:hover {
        transform: translateX(8px);
        border-left: 5px solid #10b981; /* Changes to Green on hover */
        box-shadow: 0 10px 15px rgba(0,0,0,0.08);
        background-color: #fafafa;
    }

    .card-tag {
        font-family: 'Poppins', sans-serif;
        font-size: 0.65rem;
        font-weight: 800;
        color: #2563eb;
        background: #eff6ff;
        padding: 2px 8px;
        border-radius: 5px;
    }

    .card-title {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        font-weight: 700;
        color: #1e293b;
        line-height: 1.4;
    }

    .card-footer {
        margin-top: 10px;
        font-size: 0.75rem;
        font-weight: 700;
        color: #10b981;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
            
    /* Button Styling */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white !important;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        width: 100%;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background: #2563eb !important;
        color: white !important;
    }
    
    .block-container {
        max-width: 98% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto;
    }


    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
                


    /* Turn Radio Buttons into Stable Tabs */
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        gap: 15px;
    }

    div[data-testid="stRadio"] label {
        background: white !important;
        padding: 10px 25px !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        cursor: pointer;
    }

    div[data-testid="stRadio"] label[data-selected="true"] {
        background: #2563eb !important;
        color: white !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] > label > span:first-child {
        display: none;
    }
    
    /* ONLY turn the Navigation/Hub Tabs into horizontal blocks */
    /* This targets the radio buttons inside the Hub section specifically */
    .stTabs [data-testid="stRadio"] > div, 
    .sidebar [data-testid="stRadio"] > div {
        flex-direction: row !important;
        gap: 15px;
    }

    /* Ensure Quiz Radio Buttons stay VERTICAL */
    /* We target the radio buttons that are NOT in the sidebar or specific tab containers */
    [data-testid="column"] [data-testid="stRadio"] > div {
        flex-direction: column !important;
        gap: 5px;
    }

    /* Style for the Quiz Radio Labels to make them look like clean list items */
    [data-testid="stRadio"] label {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        padding: 8px 15px !important;
        border-radius: 10px !important;
        margin-bottom: 5px !important;
        width: 100% !important;
    }
       

                            
    </style>
    """, unsafe_allow_html=True)



