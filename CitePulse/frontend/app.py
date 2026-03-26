"""
CitePulse - Academic Citation Network Analysis
Powered by Mistral AI
"""
import os
import time
import requests
import streamlit as st

# =============================================================================
# CONFIGURATION
# =============================================================================

if os.getenv("DOCKER_COMPOSE") == "true":
    API_URL = "http://api:8000"
else:
    API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

if not API_URL.endswith("/"):
    API_URL += "/"

st.set_page_config(
    page_title="CitePulse",
    layout="wide",
    page_icon="",
    initial_sidebar_state="auto"
)

# =============================================================================
# CSS
# =============================================================================

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    :root {
        --gradient-start: #6366F1;
        --gradient-mid: #8B5CF6;
        --gradient-end: #A78BFA;
        --bg-gray: #F9FAFB;
        --white: #FFFFFF;
        --gray-50: #F9FAFB;
        --gray-100: #F3F4F6;
        --gray-200: #E5E7EB;
        --gray-300: #D1D5DB;
        --gray-400: #9CA3AF;
        --gray-500: #6B7280;
        --gray-600: #4B5563;
        --gray-700: #374151;
        --gray-800: #1F2937;
        --gray-900: #111827;
    }

    .gradient-bg {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A78BFA 100%);
    }

    .main { background-color: var(--bg-gray); padding: 0; }

    .header-bar {
        background: var(--white);
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        padding: 0.75rem 0;
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 1000;
    }

    .header-content {
        max-width: 1280px;
        margin: 0 auto;
        padding: 0 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .logo-container { display: flex; align-items: center; gap: 0.5rem; }

    .logo-icon {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A78BFA 100%);
        padding: 0.5rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px; height: 36px;
    }

    .logo-text { font-size: 1.25rem; font-weight: 700; color: var(--gray-800); }

    .content-wrapper {
        max-width: 1280px;
        margin: 0 auto;
        padding: 6rem 1rem 2rem 1rem;
    }

    .hero-section {
        max-width: 56rem;
        margin: 0 auto 3rem auto;
        text-align: center;
    }

    .hero-title {
        font-size: 1.875rem;
        font-weight: 700;
        color: var(--gray-600);
        margin-bottom: 0.75rem;
        letter-spacing: 0.025em;
    }

    .hero-subtitle { font-size: 1.125rem; color: var(--gray-600); margin: 0; }

    .chat-header-icon {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A78BFA 100%);
        padding: 1rem;
        border-radius: 0.75rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 80px; height: 80px;
        margin: 0 auto;
    }

    .chat-header-icon-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
    }

    .stTextInput > div > div > input {
        border: 1px solid var(--gray-200) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        transition: all 0.2s ease !important;
        background: var(--white) !important;
        color: var(--gray-900) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
        outline: none !important;
    }

    .input-disclaimer {
        text-align: center;
        margin-top: 0.5rem;
        font-size: 0.75rem;
        color: var(--gray-500);
    }

    .stButton > button {
        background: var(--gray-900) !important;
        color: white !important;
        border: none !important;
        border-radius: 0.375rem !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }

    .stButton > button:hover { background: var(--gray-700) !important; }

    .metric-card {
        background: var(--white);
        border: 1px solid var(--gray-200);
        border-radius: 0.75rem;
        padding: 2rem;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    }

    .metric-card:hover {
        border-color: var(--gray-300);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .metric-value { font-size: 2.5rem; font-weight: 700; color: var(--gray-800); margin: 0; }
    .metric-label {
        font-size: 0.875rem; color: var(--gray-500);
        text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.5rem;
    }

    .streamlit-expanderHeader {
        background: var(--white) !important;
        border: 1px solid var(--gray-200) !important;
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
    }

    .dashboard-header {
        background: var(--white);
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        padding: 0.75rem 0;
        margin-bottom: 1rem;
    }

    .dashboard-header-content {
        max-width: 1280px;
        margin: 0 auto;
        padding: 0 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .status-indicator { display: flex; align-items: center; margin-right: 1rem; }
    .status-dot {
        width: 0.75rem; height: 0.75rem;
        border-radius: 9999px; background: #10B981; margin-right: 0.5rem;
    }
    .status-text { font-size: 0.875rem; color: var(--gray-600); }

    /* Force text visibility regardless of Streamlit theme */
    .stApp { background-color: var(--bg-gray) !important; }
    section[data-testid="stSidebar"] { background-color: var(--white) !important; }
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2,
    .stMarkdown h3, .stMarkdown h4, .stMarkdown span { color: var(--gray-900) !important; }
    label, .stRadio label, .stCheckbox label,
    .stSlider label, .stSelectbox label,
    .stTextInput label { color: var(--gray-700) !important; }
    details summary,
    details summary * {
        color: var(--gray-900) !important;
        background: transparent !important;
        background-color: transparent !important;
    }
    details summary svg {
        fill: var(--gray-900) !important;
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    details summary svg path {
        fill: var(--gray-900) !important;
    }
    details summary svg path[fill="none"],
    details summary svg path[opacity] {
        fill: none !important;
        opacity: 0 !important;
    }
    .stAlert p { color: var(--gray-900) !important; }
    .stCaption { color: var(--gray-500) !important; }
    /* Buttons: always white text regardless of other rules */
    .stButton > button,
    .stButton > button *,
    div[data-testid="stBaseButton-secondary"],
    div[data-testid="stBaseButton-secondary"] *,
    div[data-testid="stBaseButton-primary"],
    div[data-testid="stBaseButton-primary"] * { color: #FFFFFF !important; }
    /* Input fields: dark text on white background */
    input, textarea, select,
    .stTextInput input,
    .stTextArea textarea,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        color: var(--gray-900) !important;
        background-color: var(--white) !important;
    }
    input::placeholder, textarea::placeholder {
        color: var(--gray-400) !important;
    }
    /* Radio / checkbox option text */
    .stRadio div[role="radiogroup"] label p,
    .stCheckbox label p { color: var(--gray-700) !important; }

    /* === Royal purple (#6B3FA0) widget accents === */

    /* Checkbox: checked fill and border */
    label[data-baseweb="checkbox"]:has(input:checked) > span:first-child {
        background-color: #6B3FA0 !important;
        border-color: #6B3FA0 !important;
    }

    /* Radio: inner dot override to black */
    label[data-baseweb="radio"]:has(input:checked) > div:first-child > div {
        background: #111827 !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER COMPONENTS
# =============================================================================

SVG_BAR_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'


def render_header():
    st.markdown(f"""
    <div class="header-bar">
        <div class="header-content">
            <div class="logo-container">
                <div class="logo-icon">{SVG_BAR_CHART.format(w=20, h=20)}</div>
                <span class="logo-text">CitePulse</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col_login, col_signup = st.columns([6, 1, 1])
    with col_login:
        if st.button("Log in", key="header_login", use_container_width=True):
            st.session_state.show_auth = "login"
            st.rerun()
    with col_signup:
        if st.button("Sign up", key="header_signup", use_container_width=True):
            st.session_state.show_auth = "signup"
            st.rerun()


def render_dashboard_sidebar():
    user_info = st.session_state.user_info or {}
    user_name = user_info.get("full_name", "User")

    with st.sidebar:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 0.75rem; padding: 1rem 0; border-bottom: 1px solid var(--gray-200);">
            <div style="background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #A78BFA 100%); padding: 0.5rem; border-radius: 9999px; display: flex; align-items: center; justify-content: center; width: 40px; height: 40px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                </svg>
            </div>
            <div>
                <div style="font-weight: 500; color: var(--gray-800); font-size: 0.95rem;">{user_name}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='border-top: 1px solid var(--gray-200); padding-top: 1rem; margin-top: 1rem;'></div>", unsafe_allow_html=True)

        st.markdown("#### Search History")
        history = fetch_history()
        if history:
            for i, entry in enumerate(history[:20]):
                label = entry.get("paper_title") or entry.get("paper_id", "Unknown")
                if len(label) > 50:
                    label = label[:47] + "..."
                score = entry.get("consensus_score", 0)
                date_str = entry.get("created_at", "")[:10]
                if st.button(
                    f"{label}\n{date_str} | Consensus: {score}",
                    key=f"history_{i}",
                    use_container_width=True
                ):
                    st.session_state.paper_input = entry.get("paper_id", "")
                    st.session_state.search_method = "Paper ID (arXiv/DOI)"
                    st.rerun()
        else:
            st.caption("No analysis history yet.")

        st.markdown("<div style='border-top: 1px solid var(--gray-200); padding-top: 1rem; margin-top: 1rem;'></div>", unsafe_allow_html=True)

        if st.button("Log Out", key="sidebar_logout", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user_info = None
            st.session_state.analysis_data = None
            st.rerun()


def render_dashboard_header(user_name):
    st.markdown(f"""
    <div class="dashboard-header">
        <div class="dashboard-header-content">
            <div class="logo-container">
                <div class="logo-icon">{SVG_BAR_CHART.format(w=20, h=20)}</div>
                <span class="logo-text">CitePulse</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div class="status-indicator">
                    <div class="status-dot"></div>
                    <span class="status-text">Connected</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# AUTHENTICATION
# =============================================================================

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "show_auth" not in st.session_state:
    st.session_state.show_auth = None
if "history" not in st.session_state:
    st.session_state.history = None


def fetch_history():
    """Fetch analysis history for the logged-in user."""
    if not st.session_state.auth_token:
        return []
    try:
        response = requests.get(
            f"{API_URL}me/history",
            headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []


def login_user(email: str, password: str) -> bool:
    try:
        response = requests.post(
            f"{API_URL}auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.auth_token = data["access_token"]
            user_response = requests.get(
                f"{API_URL}users/me",
                headers={"Authorization": f"Bearer {st.session_state.auth_token}"}
            )
            if user_response.status_code == 200:
                st.session_state.user_info = user_response.json()
                return True
        return False
    except Exception:
        return False


def register_user(email: str, password: str, full_name: str) -> bool:
    try:
        response = requests.post(
            f"{API_URL}auth/register",
            json={"email": email, "password": password, "full_name": full_name}
        )
        return response.status_code in [200, 201]
    except Exception:
        return False


# =============================================================================
# MAIN APP
# =============================================================================

if st.session_state.show_auth == "login":
    with st.container():
        st.markdown("## Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Login", use_container_width=True):
                if login_user(email, password):
                    st.success("Logged in!")
                    st.session_state.show_auth = None
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_auth = None
                st.rerun()

elif st.session_state.show_auth == "signup":
    with st.container():
        st.markdown("## Sign Up")
        full_name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        password2 = st.text_input("Confirm Password", type="password", key="signup_password2")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Create Account", use_container_width=True):
                if not email.strip().lower().endswith(".edu"):
                    st.error("Please use a valid .edu email address. Only academic accounts are allowed.")
                elif password != password2:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                elif register_user(email, password, full_name):
                    st.success("Account created! Please login.")
                    st.session_state.show_auth = "login"
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Registration failed")
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_auth = None
                st.rerun()

else:
    is_logged_in = st.session_state.auth_token is not None

    if is_logged_in:
        render_dashboard_sidebar()
        user_name = st.session_state.user_info.get("full_name", "User") if st.session_state.user_info else "User"
        render_dashboard_header(user_name)
    else:
        render_header()

        st.markdown(f"""
        <div class="chat-header-icon-container">
            <div class="chat-header-icon">{SVG_BAR_CHART.format(w=40, h=40)}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">ANALYZE ACADEMIC PAPERS</h1>
            <p class="hero-subtitle">through citation network analysis to determine scientific consensus</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Input area (shared for both states) ---

    search_method = st.radio(
        "Search by:",
        ["Paper ID (arXiv/DOI)", "Paper Title"],
        horizontal=True,
        key="search_method"
    )

    if search_method == "Paper ID (arXiv/DOI)":
        paper_id = st.text_input(
            "",
            placeholder="e.g., 1706.03762 or 10.1038/s41586-020-2649-2",
            label_visibility="collapsed",
            key="paper_input"
        )
        paper_title = None
    else:
        paper_title = st.text_input(
            "",
            placeholder="e.g., Attention is All You Need",
            label_visibility="collapsed",
            key="title_input"
        )
        paper_id = None

    # --- Advanced Options ---
    with st.expander("Advanced Options"):
        max_papers = st.slider(
            "Number of papers to analyze",
            min_value=10, max_value=50, value=20, step=5,
            help="Maximum number of citing papers to analyze"
        )

        st.markdown("---")
        st.markdown("**Temporal Weighting:**")

        favor_option = st.radio(
            "Weight bias",
            ["Favor newer research", "Favor older research", "No temporal bias"],
            index=0,
            help="Choose whether to give more weight to recent or established research"
        )

        if favor_option != "No temporal bias":
            temporal_lambda = st.slider(
                "Temporal weight strength",
                min_value=0.01, max_value=0.20, value=0.05, step=0.01,
                help="Higher values = stronger bias"
            )
            favor_newer = favor_option == "Favor newer research"
        else:
            temporal_lambda = 0.0
            favor_newer = True

        st.markdown("---")
        st.markdown("**Authorship Bias:**")

        apply_authorship_bias = st.checkbox(
            "Reduce weight for self-citations",
            value=True,
            help="Citations from papers sharing authors with the original work receive reduced weight"
        )

        if apply_authorship_bias:
            authorship_penalty = st.slider(
                "Self-citation weight penalty",
                min_value=0.0, max_value=1.0, value=0.5, step=0.05,
                help="0.0 = ignore self-citations completely, 1.0 = no penalty"
            )
        else:
            authorship_penalty = 1.0

        st.markdown("---")
        st.markdown("**Bibliometric Weighting:**")
        st.caption("Weight citations using non-proprietary academic metrics from Semantic Scholar.")

        metric_col1, metric_col2 = st.columns(2)
        with metric_col1:
            use_citation_count = st.checkbox(
                "Citation count",
                value=False,
                help="Weight by how many times the citing paper has been cited",
                key="use_citation_count"
            )
            use_influential_citations = st.checkbox(
                "Influential citation count",
                value=False,
                help="Weight by Semantic Scholar's influential citation metric",
                key="use_influential_citations"
            )
        with metric_col2:
            use_author_hindex = st.checkbox(
                "Author h-index",
                value=False,
                help="Weight by the max h-index among the citing paper's authors",
                key="use_author_hindex"
            )
            use_reference_count = st.checkbox(
                "Reference count",
                value=False,
                help="Weight by the number of references in the citing paper (higher may indicate review papers)",
                key="use_reference_count"
            )

        any_metric_selected = use_citation_count or use_influential_citations or use_author_hindex or use_reference_count

        invert_metrics = False
        if any_metric_selected:
            invert_metrics = st.checkbox(
                "Invert metric weights (prioritize lower-metric citations)",
                value=False,
                help="When enabled, citations from less-cited papers, newer authors, or smaller venues receive MORE weight. Useful for discovering emerging or underrepresented research.",
                key="invert_metrics"
            )

        st.markdown("---")
        st.markdown("**Filter by category:**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            filter_support = st.checkbox("Support", value=True, key="filter_support")
        with col2:
            filter_extend = st.checkbox("Extend", value=True, key="filter_extend")
        with col3:
            filter_neutral = st.checkbox("Neutral", value=True, key="filter_neutral")
        with col4:
            filter_refute = st.checkbox("Refute", value=True, key="filter_refute")

        if not any([filter_support, filter_extend, filter_neutral, filter_refute]):
            st.warning("No categories selected. All categories will be included.")
            category_filters = ["support", "extend", "neutral", "refute"]
        else:
            category_filters = []
            if filter_support:
                category_filters.append("support")
            if filter_extend:
                category_filters.append("extend")
            if filter_neutral:
                category_filters.append("neutral")
            if filter_refute:
                category_filters.append("refute")

    st.markdown("""
    <p class="input-disclaimer">
        CitePulse uses Mistral AI for citation classification and Semantic Scholar for paper data.
    </p>
    """, unsafe_allow_html=True)

    # --- Analyze button ---
    if st.button("Analyze Paper", use_container_width=False):
        if paper_id or paper_title:
            with st.spinner("Analyzing citations..."):
                try:
                    headers = {}
                    if st.session_state.auth_token:
                        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

                    payload = {
                        "max_citations": max_papers,
                        "category_filters": category_filters,
                        "use_temporal_weighting": temporal_lambda > 0,
                        "use_temporal_distribution": True,
                        "temporal_lambda": temporal_lambda,
                        "favor_newer": favor_newer,
                        "apply_authorship_bias": apply_authorship_bias,
                        "authorship_penalty": authorship_penalty,
                        "use_citation_count_weight": use_citation_count,
                        "use_influential_citation_weight": use_influential_citations,
                        "use_author_hindex_weight": use_author_hindex,
                        "use_reference_count_weight": use_reference_count,
                        "invert_metric_weights": invert_metrics,
                    }

                    if paper_id:
                        payload["paper_id"] = paper_id
                    else:
                        payload["paper_title"] = paper_title

                    response = requests.post(
                        f"{API_URL}analyze",
                        json=payload,
                        headers=headers if headers else None,
                        timeout=180
                    )

                    if response.status_code == 200:
                        st.session_state.analysis_data = response.json()
                        st.session_state.category_filters = category_filters
                        st.rerun()
                    elif response.status_code == 401:
                        st.error("Please login to analyze papers")
                        st.session_state.show_auth = "login"
                        st.rerun()
                    else:
                        detail = response.json().get("detail", response.text)
                        st.error(f"Error: {detail}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a paper ID or title")

    # --- Results section ---
    if "analysis_data" in st.session_state and st.session_state.analysis_data:
        data = st.session_state.analysis_data

        if data.get("is_retracted"):
            if data.get("paper_title"):
                st.warning(f"**{data['paper_title']}**")
                st.caption(f"Paper ID: `{data.get('paper_id', 'N/A')}`")

            st.error("### RETRACTED PAPER")
            st.error(data.get("retraction_notice", "This paper has been retracted and should not be cited."))
            st.markdown("""
            **What does this mean?**
            - This paper has been officially withdrawn from the scientific record
            - The findings are considered unreliable and should not be used
            - No further citation analysis is performed for retracted papers
            """)

        elif data.get("items"):
            st.markdown("### Results")

            if data.get("paper_title"):
                st.info(f"**{data['paper_title']}**")
                st.caption(f"Paper ID: `{data.get('paper_id', 'N/A')}`")
            elif data.get("paper_id"):
                st.info(f"Analyzed Paper ID: `{data['paper_id']}`")

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{data["counts"]["support"]}</div>
                    <div class="metric-label">Support</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{data["counts"]["extend"]}</div>
                    <div class="metric-label">Extend</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{data["counts"]["neutral"]}</div>
                    <div class="metric-label">Neutral</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{data["counts"]["refute"]}</div>
                    <div class="metric-label">Refute</div>
                </div>
                """, unsafe_allow_html=True)

            with col5:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{data["consensus_score"]}</div>
                    <div class="metric-label">Consensus</div>
                </div>
                """, unsafe_allow_html=True)

            # Trend Analysis
            if data.get("trend_analysis"):
                st.markdown("---")
                st.markdown("### Citation Trend Analysis")

                trend = data["trend_analysis"]
                trend_icons = {
                    "trending_up": "Trending Up",
                    "declining": "Declining",
                    "stable": "Stable"
                }
                trend_colors = {
                    "trending_up": "#00cc00",
                    "declining": "#6c757d",
                    "stable": "#ffaa00"
                }

                icon = trend_icons.get(trend["trend_direction"], "Stable")
                color = trend_colors.get(trend["trend_direction"], "#ffaa00")

                st.markdown(f"""
                <div style="background-color: {color}22; border-left: 4px solid {color}; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: {color};">{icon}</h3>
                    <p style="margin: 5px 0 0 0; color: #666;">{trend["explanation"]}</p>
                    <p style="margin: 10px 0 0 0; font-size: 0.9em; color: #888;">
                        Recent (last 3 years): {trend["recent_citations_count"]} citations |
                        Historical: {trend["historical_citations_count"]} citations |
                        Momentum Score: {trend["momentum_score"]}x
                    </p>
                </div>
                """, unsafe_allow_html=True)

                # Timeline scatter plot
                if data.get("items"):
                    import pandas as pd
                    import plotly.graph_objects as go

                    citation_data = []
                    category_map = {
                        "support": "Support",
                        "extend": "Extend",
                        "neutral": "Neutral",
                        "refute": "Refute"
                    }

                    for item in data["items"]:
                        year = item.get("year")
                        polarity = item.get("polarity", "neutral")
                        if year:
                            citation_data.append({
                                "year": year,
                                "category": category_map.get(polarity, "Neutral")
                            })

                    if citation_data:
                        df = pd.DataFrame(citation_data)
                        fig = go.Figure()

                        colors = {
                            "Support": "#28a745",
                            "Extend": "#007bff",
                            "Neutral": "#6c757d",
                            "Refute": "#dc3545"
                        }

                        for category in ["Support", "Extend", "Neutral", "Refute"]:
                            category_df = df[df["category"] == category]
                            if not category_df.empty:
                                year_counts = category_df.groupby("year").size().reset_index(name="count")
                                fig.add_trace(go.Scatter(
                                    x=year_counts["year"],
                                    y=year_counts["count"],
                                    mode="markers",
                                    name=category,
                                    marker=dict(
                                        size=10,
                                        color=colors[category],
                                        line=dict(width=1, color="white")
                                    )
                                ))

                        fig.update_layout(
                            title="Citations Over Time by Category",
                            xaxis_title="Year",
                            yaxis_title="Number of Citations",
                            height=400,
                            hovermode="closest",
                            xaxis=dict(type="linear", dtick=1),
                            yaxis=dict(dtick=1)
                        )
                        st.plotly_chart(fig, use_container_width=True)

            # Citations by category
            st.markdown("---")
            st.markdown("### Citations by Category")

            categorized_items = {"support": [], "extend": [], "neutral": [], "refute": []}
            for item in data["items"]:
                polarity = item.get("polarity", "neutral").lower()
                if polarity in categorized_items:
                    categorized_items[polarity].append(item)

            category_labels = {
                "support": "Supporting Papers",
                "extend": "Extending Papers",
                "neutral": "Neutral Papers",
                "refute": "Refuting Papers"
            }

            for category, label in category_labels.items():
                items = categorized_items[category]
                if items:
                    with st.expander(f"{label} ({len(items)})", expanded=(category == "support")):
                        for item in items:
                            st.markdown(f"**{item.get('title', 'Citation')}**")
                            st.markdown(f"*Classification:* {item['polarity'].title()} (Confidence: {item['confidence']:.2f})")
                            if item.get('year'):
                                st.markdown(f"*Year:* {item['year']}")

                            # Display bibliometric data if available
                            metrics_parts = []
                            if item.get('citation_count') is not None:
                                metrics_parts.append(f"Citations: {item['citation_count']}")
                            if item.get('influential_citation_count') is not None:
                                metrics_parts.append(f"Influential: {item['influential_citation_count']}")
                            if item.get('author_hindex') is not None:
                                metrics_parts.append(f"Author h-index: {item['author_hindex']}")
                            if item.get('reference_count') is not None:
                                metrics_parts.append(f"References: {item['reference_count']}")
                            if metrics_parts:
                                st.caption(" | ".join(metrics_parts))

                            st.markdown(f"*Explanation:* {item['explanation']}")
                            st.markdown(f"> {item['snippet']}")
                            st.markdown("---")
