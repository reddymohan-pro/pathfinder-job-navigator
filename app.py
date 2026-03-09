import streamlit as st
import pandas as pd
import os, sys
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from recommender import load_data, get_jobs_unlocked, recommend_next_skill, get_country_skill_gap, get_salary_for_skills
from resume_parser import parse_resume_text, parse_pdf_resume, parse_txt_resume
from skill_extractor import ALL_SKILL_NAMES

st.set_page_config(page_title="Job Navigator", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

# ════════════════════════════════════════════════════════════════
# COLOR PSYCHOLOGY CSS
# Navy = trust/authority | Emerald = growth/money | Amber = action
# Warm near-black bg = premium, not cold
# ════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── ROOT VARIABLES ── */
:root {
    --bg-base:      #0d1117;
    --bg-card:      #161b22;
    --bg-card-hover:#1c2330;
    --navy:         #1a3a5c;
    --navy-light:   #2563a8;
    --emerald:      #10b981;
    --emerald-dim:  #065f46;
    --amber:        #f59e0b;
    --amber-dim:    #78350f;
    --red-soft:     #ef4444;
    --text-primary: #e6edf3;
    --text-muted:   #8b949e;
    --border:       #21262d;
    --india-saffron:#ff9933;
    --usa-blue:     #3b82f6;
    --gold:         #fbbf24;
}

/* ── GLOBAL ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2e 0%, #0d1117 60%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* ── MAIN BACKGROUND ── */
.main .block-container {
    background: var(--bg-base);
    padding-top: 2rem !important;
}

/* ── HEADER HERO ── */
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3rem;
    font-weight: 400;
    background: linear-gradient(135deg, #e6edf3 0%, var(--emerald) 50%, var(--amber) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    margin-bottom: 0.25rem;
}
.hero-sub {
    color: var(--text-muted);
    font-size: 1.1rem;
    font-weight: 300;
    letter-spacing: 0.02em;
}

/* ── METRIC CARDS (top 4) ── */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1.2rem 1.4rem !important;
    transition: border-color 0.2s ease;
}
[data-testid="metric-container"]:hover {
    border-color: var(--emerald) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-family: 'DM Serif Display', serif !important;
    font-size: 2.2rem !important;
}
[data-testid="stMetricDelta"] {
    color: var(--emerald) !important;
}

/* ── SECTION HEADERS ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--emerald);
    margin-bottom: 0.3rem;
}
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.8rem;
    color: var(--text-primary);
    margin-bottom: 1.2rem;
    font-weight: 400;
}

/* ── JOB CARDS ── */
.job-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
    border-left: 4px solid var(--emerald);
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}
.job-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, var(--emerald), transparent);
    opacity: 0.4;
}
.job-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--emerald);
    transform: translateX(3px);
}
.job-card-amber { border-left-color: var(--amber); }
.job-card-amber::before { background: linear-gradient(90deg, var(--amber), transparent); }
.job-card-red { border-left-color: #4a1515; }

.job-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.05rem;
    color: var(--text-primary);
    font-weight: 400;
}
.job-company { color: var(--text-muted); font-size: 0.9rem; }

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    margin: 0 3px;
}
.badge-match  { background: rgba(16,185,129,0.12); color: var(--emerald); border: 1px solid rgba(16,185,129,0.25); }
.badge-amber  { background: rgba(245,158,11,0.12); color: var(--amber);   border: 1px solid rgba(245,158,11,0.25); }
.badge-fresher{ background: rgba(16,185,129,0.08); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.2); }
.badge-senior { background: rgba(239,68,68,0.08);  color: #fca5a5; border: 1px solid rgba(239,68,68,0.2); }
.badge-grey   { background: rgba(139,148,158,0.1); color: var(--text-muted); border: 1px solid rgba(139,148,158,0.2); }

.skill-chip {
    display: inline-block;
    background: rgba(37,99,168,0.15);
    color: #93c5fd;
    border: 1px solid rgba(37,99,168,0.3);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.72rem;
    margin: 2px;
}
.skill-chip-missing {
    background: rgba(239,68,68,0.08);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.2);
}

.apply-btn {
    display: inline-block;
    margin-top: 10px;
    padding: 6px 16px;
    background: linear-gradient(135deg, var(--emerald-dim), #0d4f38);
    border: 1px solid var(--emerald);
    border-radius: 6px;
    color: var(--emerald) !important;
    font-size: 0.8rem;
    font-weight: 500;
    text-decoration: none;
    letter-spacing: 0.03em;
    transition: all 0.15s ease;
}
.apply-btn:hover {
    background: var(--emerald);
    color: #000 !important;
}

/* ── DIVIDER ── */
.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border) 20%, var(--border) 80%, transparent);
    margin: 2.5rem 0;
}

/* ── INDIA/USA FLAGS ── */
.country-india { color: var(--india-saffron); font-weight: 600; }
.country-usa   { color: var(--usa-blue);      font-weight: 600; }
.country-remote{ color: var(--text-muted);    font-weight: 500; }

/* ── STREAMLIT OVERRIDES ── */
.stSlider [data-baseweb="slider"] div div div div {
    background: var(--emerald) !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(37,99,168,0.25) !important;
    border: 1px solid var(--navy-light) !important;
}
[data-testid="stCheckbox"] label { color: var(--text-primary) !important; }
.stSelectbox [data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border) !important;
}

/* ── SIDEBAR LOGO AREA ── */
.sidebar-logo {
    text-align: center;
    padding: 1rem 0 0.5rem;
}
.sidebar-logo-icon {
    font-size: 2.5rem;
    display: block;
    margin-bottom: 0.3rem;
}
.sidebar-logo-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.4rem;
    color: var(--text-primary);
}
.sidebar-logo-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── STAT BAR ── */
.stat-bar {
    display: flex;
    gap: 1.5rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem 1.4rem;
    margin-bottom: 1.5rem;
    font-size: 0.82rem;
    color: var(--text-muted);
}
.stat-bar strong { color: var(--emerald); }

/* ── SALARY NUMBER HIGHLIGHT ── */
.salary-big {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: var(--gold);
}
.salary-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }

/* ── ALERTS ── */
[data-testid="stAlert"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* ── PLOTLY CHART CONTAINERS ── */
[data-testid="stPlotlyChart"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border);
}
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# DATA LOADING
# ════════════════════════════════════════
@st.cache_data(ttl=3600)
def load_all():
    jobs = load_data()
    freq_path = os.path.join("data","skill_frequency.csv")
    freq = pd.read_csv(freq_path) if os.path.exists(freq_path) else pd.DataFrame()
    return jobs, freq

def last_updated():
    p = os.path.join("data","last_updated.txt")
    return open(p).read().strip() if os.path.exists(p) else "Unknown"

df, skill_freq = load_all()

# ════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════
st.sidebar.markdown("""
<div class="sidebar-logo">
  <span class="sidebar-logo-icon">🎯</span>
  <div class="sidebar-logo-title">Job Navigator</div>
  <div class="sidebar-logo-sub">Fresh Graduate Edition</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Upload Your Resume")
st.sidebar.caption("We auto-detect your skills from PDF or TXT")
uploaded = st.sidebar.file_uploader("", type=["pdf","txt"], label_visibility="collapsed")

auto_skills = []
if uploaded:
    with st.spinner("Reading your resume..."):
        text = parse_pdf_resume(uploaded) if uploaded.type == "application/pdf" else parse_txt_resume(uploaded)
        if text:
            result = parse_resume_text(text)
            auto_skills = result["skills_found"]
            st.sidebar.success(f"✅ {len(auto_skills)} skills detected automatically")
            st.sidebar.caption(f"Profile level: **{result['experience_level'].title()}**")
        else:
            st.sidebar.warning("Couldn't read the file. Add skills manually below.")

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Your Skills")
user_skills = st.sidebar.multiselect(
    "Select everything you know:",
    options=sorted(ALL_SKILL_NAMES),
    default=sorted(list(set(auto_skills))) if auto_skills else ["python", "sql"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Target Market")
target_country = st.sidebar.selectbox(
    "Where do you want to work?",
    ["All","India","USA","Remote"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎓 Experience Filter")
fresher_only = st.sidebar.checkbox("Fresher Friendly jobs only", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style='font-size:0.78rem; color:#8b949e; line-height:1.8'>
🗃️ Jobs in database: <strong style='color:#10b981'>{len(df)}</strong><br>
🕐 Last updated: <strong style='color:#e6edf3'>{last_updated()}</strong><br>
🔄 Auto-refreshes every 24 hours
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# MAIN CONTENT
# ════════════════════════════════════════

# Hero header
st.markdown("""
<div style='padding: 1rem 0 0.5rem'>
  <div class="hero-title">Find your next opportunity.<br>Before anyone else does.</div>
  <div class="hero-sub">Real jobs from India & USA, matched to your skills — updated daily.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

if not user_skills:
    st.warning("👈 Select at least one skill from the sidebar to get started.")
    st.stop()

# Filter data
df_f = df[df["country"].isin([target_country,"Remote"])] if target_country != "All" else df.copy()
if fresher_only:
    df_f = df_f[df_f["experience_level"].isin(["fresher","unknown"])]

matched    = get_jobs_unlocked(user_skills, df_f)
recs       = recommend_next_skill(user_skills, df_f)
salary_inf = get_salary_for_skills(user_skills, target_country)

# ── TOP METRICS ────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Jobs You Qualify For", f"{len(matched):,}", help="Based on your current skill set")
col2.metric("Skills You Have", len(user_skills))
col3.metric("Best Next Skill", recs[0]["skill"].title() if recs else "—",
            delta=f"+{recs[0]['new_jobs_unlocked']} jobs" if recs else None)
col4.metric("Market", target_country)

st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# SECTION 1 — JOBS
# ════════════════════════════════════════════════
st.markdown("<div class='section-label'>Live Opportunities</div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Jobs You Qualify For Right Now</div>", unsafe_allow_html=True)

if not matched:
    st.warning("No jobs matched. Try adding more skills or switching market to **All**.")
else:
    col_a, col_b = st.columns([1,1])
    min_match = col_a.slider("Minimum match %", 40, 100, 60, step=10)
    show_n    = col_b.selectbox("Show top", [10,25,50,100], index=1)

    visible = [j for j in matched if j["match_score"] >= min_match][:show_n]

    # Country color map
    COUNTRY_CLASS = {"India": "country-india", "USA": "country-usa", "Remote": "country-remote"}

    EXP_BADGE = {
        "fresher": ('<span class="badge badge-fresher">🟢 Fresher Friendly</span>', "job-card"),
        "junior":  ('<span class="badge badge-amber">🟡 Junior (1-3 yrs)</span>',   "job-card job-card-amber"),
        "mid":     ('<span class="badge badge-amber">🟠 Mid (3-6 yrs)</span>',       "job-card job-card-amber"),
        "senior":  ('<span class="badge badge-senior">🔴 Senior (6+ yrs)</span>',   "job-card job-card-red"),
    }

    if not visible:
        st.info("No jobs at this match threshold. Lower the minimum match %.")
    else:
        for job in visible:
            score      = job["match_score"]
            exp        = job.get("experience_level","unknown")
            exp_badge, card_css = EXP_BADGE.get(exp, ('<span class="badge badge-grey">⚪ Not Specified</span>', "job-card"))

            # Match badge color
            if score >= 80:
                match_badge = f'<span class="badge badge-match">{score}% match</span>'
            else:
                match_badge = f'<span class="badge badge-amber">{score}% match</span>'

            country_cls = COUNTRY_CLASS.get(job["country"], "country-remote")

            # Build skill chips
            matched_chips = "".join(f'<span class="skill-chip">{s}</span>' for s in job["matched_skills"])
            if job["missing_skills"]:
                missing_chips = "".join(f'<span class="skill-chip skill-chip-missing">{s}</span>' for s in job["missing_skills"])
                missing_row = f'<div style="margin-top:6px"><span style="font-size:0.75rem;color:#8b949e">Missing: </span>{missing_chips}</div>'
            else:
                missing_row = '<div style="margin-top:6px"><span style="font-size:0.75rem;color:#10b981">✓ Perfect match — you have every required skill</span></div>'

            apply_btn = f'<a href="{job["url"]}" target="_blank" class="apply-btn">→ Apply Now</a>' if job.get("url") else ""

            st.markdown(f"""
<div class="{card_css}">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:8px">
    <div>
      <div class="job-title">{job['title']}</div>
      <div class="job-company" style="margin-top:3px">{job['company']} · <span class="{country_cls}">{job['country']}</span></div>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center">
      {match_badge}
      {exp_badge}
    </div>
  </div>
  <div style="margin-top:10px">
    <span style="font-size:0.75rem;color:#8b949e">Matched: </span>{matched_chips}
    {missing_row}
  </div>
  {apply_btn}
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# SECTION 2 — WHAT TO LEARN NEXT
# ════════════════════════════════════════════════
st.markdown("<div class='section-label'>Career Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>What To Learn Next</div>", unsafe_allow_html=True)

if not recs:
    st.success("You're maximally qualified for the current dataset. Add more skills to explore further.")
else:
    col_a, col_b = st.columns([1,1])
    with col_a:
        for i, rec in enumerate(recs):
            st.metric(
                label=f"#{i+1}  {rec['skill'].title()}",
                value=f"+{rec['new_jobs_unlocked']} new jobs",
                delta=f"Reach {rec['total_jobs']} total jobs"
            )

    with col_b:
        rec_df = pd.DataFrame(recs)
        fig = go.Figure(go.Bar(
            x=rec_df["new_jobs_unlocked"],
            y=rec_df["skill"],
            orientation="h",
            marker=dict(
                color=rec_df["new_jobs_unlocked"],
                colorscale=[[0,"#065f46"],[0.5,"#10b981"],[1,"#6ee7b7"]],
                showscale=False
            ),
            text=[f"+{v}" for v in rec_df["new_jobs_unlocked"]],
            textposition="outside",
            textfont=dict(color="#10b981", size=12)
        ))
        fig.update_layout(
            title=dict(text="New jobs unlocked per skill", font=dict(color="#8b949e", size=13)),
            yaxis=dict(autorange="reversed", color="#8b949e", tickfont=dict(size=12)),
            xaxis=dict(color="#8b949e", showgrid=True, gridcolor="#21262d"),
            plot_bgcolor="#161b22",
            paper_bgcolor="#161b22",
            font=dict(color="#e6edf3"),
            margin=dict(l=10,r=60,t=40,b=20),
            height=280
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# SECTION 3 — SALARY
# ════════════════════════════════════════════════
st.markdown("<div class='section-label'>Earning Potential</div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Salary Insights For Your Skills</div>", unsafe_allow_html=True)

if salary_inf.empty:
    msgs = {
        "Remote": "💡 Remote salaries are rarely listed publicly. Switch to **India** or **USA** to see data.",
        "All":    "💡 Select **India** or **USA** in the sidebar to see salary data for your skills."
    }
    st.info(msgs.get(target_country, "💡 No salary data for these skills yet. Try Python, Machine Learning, or AWS."))
else:
    col_a, col_b = st.columns([1,1])
    with col_a:
        for _, row in salary_inf.iterrows():
            flag = "🇮🇳" if row["country"] == "India" else "🇺🇸"
            currency_color = "#ff9933" if row["country"] == "India" else "#3b82f6"
            st.markdown(f"""
<div style='background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px 20px;margin-bottom:10px;border-left:4px solid {currency_color}'>
  <div class='salary-label'>{flag} {row['skill'].title()} · {row['country']}</div>
  <div class='salary-big'>{row['salary_formatted']}</div>
  <div style='font-size:0.75rem;color:#8b949e;margin-top:4px'>Average across {int(row['job_count'])} jobs</div>
</div>
""", unsafe_allow_html=True)

    with col_b:
        fig = go.Figure()
        for country, color in [("India","#ff9933"),("USA","#3b82f6")]:
            subset = salary_inf[salary_inf["country"] == country]
            if not subset.empty:
                fig.add_trace(go.Bar(
                    name=country,
                    x=subset["avg_salary"],
                    y=subset["skill"],
                    orientation="h",
                    marker_color=color,
                    marker_opacity=0.85,
                    text=subset["salary_formatted"],
                    textposition="outside",
                    textfont=dict(color=color, size=11)
                ))
        fig.update_layout(
            barmode="group",
            title=dict(text="Average salary by skill & market", font=dict(color="#8b949e", size=13)),
            yaxis=dict(autorange="reversed", color="#8b949e"),
            xaxis=dict(color="#8b949e", showgrid=True, gridcolor="#21262d"),
            plot_bgcolor="#161b22",
            paper_bgcolor="#161b22",
            font=dict(color="#e6edf3"),
            legend=dict(bgcolor="#161b22", bordercolor="#21262d", borderwidth=1),
            margin=dict(l=10,r=120,t=40,b=20),
            height=320
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# SECTION 4 — INDIA VS USA
# ════════════════════════════════════════════════
st.markdown("<div class='section-label'>Market Intelligence</div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>🇮🇳 India vs USA 🇺🇸 Skill Demand</div>", unsafe_allow_html=True)

gap_df = get_country_skill_gap(df)
col_a, col_b = st.columns(2)

def make_bar(df_in, x_col, y_col, title, color):
    fig = go.Figure(go.Bar(
        x=df_in[x_col],
        y=df_in[y_col],
        orientation="h",
        marker_color=color,
        marker_opacity=0.8,
        text=df_in[x_col],
        textposition="outside",
        textfont=dict(color=color, size=11)
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color="#8b949e", size=13)),
        yaxis=dict(autorange="reversed", color="#8b949e", tickfont=dict(size=11)),
        xaxis=dict(color="#8b949e", showgrid=True, gridcolor="#21262d"),
        plot_bgcolor="#161b22",
        paper_bgcolor="#161b22",
        font=dict(color="#e6edf3"),
        margin=dict(l=10,r=50,t=40,b=20),
        showlegend=False,
        height=340
    )
    return fig

with col_a:
    top = gap_df.nlargest(10,"india_count")[["skill","india_count"]]
    st.plotly_chart(make_bar(top,"india_count","skill","Top 10 skills in India","#ff9933"), use_container_width=True)

with col_b:
    top = gap_df.nlargest(10,"usa_count")[["skill","usa_count"]]
    st.plotly_chart(make_bar(top,"usa_count","skill","Top 10 skills in USA","#3b82f6"), use_container_width=True)

# Gap chart
gap_pos = gap_df[gap_df["gap"] > 0].head(12)
fig = go.Figure(go.Bar(
    x=gap_pos["gap"],
    y=gap_pos["skill"],
    orientation="h",
    marker=dict(
        color=gap_pos["gap"],
        colorscale=[[0,"#ff9933"],[1,"#fbbf24"]],
        showscale=False
    ),
    text=gap_pos["gap"],
    textposition="outside",
    textfont=dict(color="#fbbf24", size=11)
))
fig.update_layout(
    title=dict(text="Skills India demands significantly more than USA — if you're targeting India, these are non-negotiable",
               font=dict(color="#8b949e", size=13)),
    yaxis=dict(autorange="reversed", color="#8b949e"),
    xaxis=dict(color="#8b949e", showgrid=True, gridcolor="#21262d"),
    plot_bgcolor="#161b22",
    paper_bgcolor="#161b22",
    font=dict(color="#e6edf3"),
    margin=dict(l=10,r=50,t=50,b=20),
    showlegend=False,
    height=320
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════
# SECTION 5 — MARKET TRENDS
# ════════════════════════════════════════════════
st.markdown("<div class='section-label'>Macro Trends</div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>Overall Market Skill Demand</div>", unsafe_allow_html=True)

if not skill_freq.empty:
    top25 = skill_freq.head(25)
    colors = ["#10b981" if s in user_skills else "#2563a8" for s in top25["skill"]]

    fig = go.Figure(go.Bar(
        x=top25["count"],
        y=top25["skill"],
        orientation="h",
        marker_color=colors,
        marker_opacity=0.85,
        text=top25["count"],
        textposition="outside",
        textfont=dict(color="#8b949e", size=10)
    ))
    fig.update_layout(
        title=dict(
            text="Top 25 most demanded skills · <span style='color:#10b981'>■</span> Green = skills you already have",
            font=dict(color="#8b949e", size=13)
        ),
        yaxis=dict(autorange="reversed", color="#8b949e", tickfont=dict(size=11)),
        xaxis=dict(color="#8b949e", showgrid=True, gridcolor="#21262d"),
        plot_bgcolor="#161b22",
        paper_bgcolor="#161b22",
        font=dict(color="#e6edf3"),
        margin=dict(l=10,r=60,t=50,b=20),
        showlegend=False,
        height=620
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("🟢 Green bars = skills you already have · 🔵 Blue bars = skills to consider learning")

st.markdown("<div class='fancy-divider'></div>", unsafe_allow_html=True)

# Footer
st.markdown(f"""
<div style='text-align:center;padding:1.5rem 0;color:#8b949e;font-size:0.8rem;letter-spacing:0.04em'>
  Built for fresh graduates navigating India & USA job markets<br>
  <span style='color:#21262d'>·</span>
  Data: Adzuna + Jobicy APIs
  <span style='color:#21262d'>·</span>
  Last updated: {last_updated()}
  <span style='color:#21262d'>·</span>
  Refreshes every 24 hours
</div>
""", unsafe_allow_html=True)