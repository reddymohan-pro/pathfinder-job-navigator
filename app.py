import streamlit as st
import pandas as pd
import os, sys
import plotly.express as px

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from recommender import load_data, get_jobs_unlocked, recommend_next_skill, get_country_skill_gap, get_salary_for_skills
from resume_parser import parse_resume_text, parse_pdf_resume, parse_txt_resume
from skill_extractor import ALL_SKILL_NAMES

st.set_page_config(page_title="Pathfinder", page_icon="🎯", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif !important; }

.stApp { background: #08090c; color: #f0f4ff; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0f14 0%, #08090c 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}

section[data-testid="stSidebar"] * { color: #f0f4ff !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #161b26;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 20px !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 36px !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #a78bfa, #f9a8d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

[data-testid="stMetricLabel"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #4a5568 !important;
}

[data-testid="stMetricDelta"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
}

/* Job cards */
.job-card {
    background: #161b26;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 10px;
    transition: all 0.2s;
    border-left: 3px solid #10b981;
}
.job-card-amber { border-left: 3px solid #f59e0b !important; }
.job-card-rose  { border-left: 3px solid #f43f5e !important; }

.job-title { font-size: 15px; font-weight: 700; color: #f0f4ff; letter-spacing: -0.2px; margin-bottom: 8px; }
.job-meta  { font-family: 'Space Mono', monospace; font-size: 11px; color: #8892aa; margin-bottom: 10px; }

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 100px;
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    margin-right: 5px;
    margin-bottom: 5px;
}
.badge-in  { background: rgba(255,107,0,0.12); color: #ff9950; border: 1px solid rgba(255,107,0,0.25); }
.badge-us  { background: rgba(59,130,246,0.12); color: #93c5fd; border: 1px solid rgba(59,130,246,0.25); }
.badge-re  { background: rgba(255,255,255,0.05); color: #4a5568; border: 1px solid rgba(255,255,255,0.1); }
.badge-fr  { background: rgba(16,185,129,0.12); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.25); }
.badge-jr  { background: rgba(245,158,11,0.12); color: #fcd34d; border: 1px solid rgba(245,158,11,0.25); }
.badge-md  { background: rgba(251,146,60,0.12); color: #fdba74; border: 1px solid rgba(251,146,60,0.25); }
.badge-sr  { background: rgba(244,63,94,0.12);  color: #fda4af; border: 1px solid rgba(244,63,94,0.25); }
.badge-uk  { background: rgba(255,255,255,0.04); color: #4a5568; border: 1px solid rgba(255,255,255,0.08); }
.badge-sc  { background: rgba(167,139,250,0.12); color: #a78bfa; border: 1px solid rgba(167,139,250,0.25); margin-right:4px; }
.badge-sm  { background: rgba(244,63,94,0.1);    color: #fda4af; border: 1px solid rgba(244,63,94,0.2);   margin-right:4px; }

.score-high   { font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:700; color:#10b981; }
.score-medium { font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:700; color:#f59e0b; }
.score-low    { font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:700; color:#f43f5e; }

/* Rec cards */
.rec-card {
    border-radius: 14px;
    padding: 22px 20px;
    margin-bottom: 10px;
    cursor: pointer;
}
.rc1 { background: linear-gradient(135deg, rgba(124,58,237,0.2), rgba(236,72,153,0.15)); border: 1px solid rgba(167,139,250,0.2); }
.rc2 { background: linear-gradient(135deg, rgba(6,182,212,0.18), rgba(16,185,129,0.15)); border: 1px solid rgba(103,232,249,0.2); }
.rc3 { background: linear-gradient(135deg, rgba(245,158,11,0.18), rgba(251,146,60,0.15)); border: 1px solid rgba(252,211,77,0.2); }
.rc4 { background: linear-gradient(135deg, rgba(236,72,153,0.18), rgba(244,63,94,0.12)); border: 1px solid rgba(249,168,212,0.2); }
.rc5 { background: linear-gradient(135deg, rgba(16,185,129,0.18), rgba(6,182,212,0.12)); border: 1px solid rgba(110,231,183,0.2); }

.rec-num { font-size: 38px; font-weight: 700; letter-spacing: -2px; line-height: 1; }
.rc1 .rec-num { background: linear-gradient(135deg,#a78bfa,#f9a8d4); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.rc2 .rec-num { background: linear-gradient(135deg,#67e8f9,#6ee7b7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.rc3 .rec-num { background: linear-gradient(135deg,#fcd34d,#fb923c); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.rc4 .rec-num { background: linear-gradient(135deg,#f9a8d4,#fda4af); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.rc5 .rec-num { background: linear-gradient(135deg,#6ee7b7,#67e8f9); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }

.rec-skill { font-size: 16px; font-weight: 700; color: #f0f4ff; letter-spacing: -0.3px; margin: 6px 0 4px; text-transform: capitalize; }
.rec-tag   { font-family: 'Space Mono', monospace; font-size: 9px; color: #4a5568; letter-spacing: 0.1em; text-transform: uppercase; }

/* Salary cards */
.sal-card { border-radius: 14px; padding: 20px; margin-bottom: 10px; }
.sal-india { background: linear-gradient(135deg, rgba(255,107,0,0.18), rgba(245,158,11,0.12)); border: 1px solid rgba(255,107,0,0.2); }
.sal-usa   { background: linear-gradient(135deg, rgba(59,130,246,0.18), rgba(124,58,237,0.12)); border: 1px solid rgba(59,130,246,0.2); }
.sal-skill  { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:0.12em; text-transform:uppercase; color:#4a5568; margin-bottom:6px; }
.sal-amount-india { font-size:26px; font-weight:700; background:linear-gradient(90deg,#ff9950,#fcd34d); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin-bottom:4px; }
.sal-amount-usa   { font-size:26px; font-weight:700; background:linear-gradient(90deg,#93c5fd,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; margin-bottom:4px; }
.sal-meta  { font-family:'Space Mono',monospace; font-size:10px; color:#4a5568; }

/* Section headers */
.sec-header {
    font-size: 20px;
    font-weight: 700;
    color: #f0f4ff;
    letter-spacing: -0.3px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}

/* Hero */
.hero {
    background: linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(236,72,153,0.1) 50%, rgba(6,182,212,0.08) 100%);
    border-bottom: 1px solid rgba(255,255,255,0.07);
    padding: 48px 48px 36px;
}
.hero-title {
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -1.5px;
    line-height: 1.1;
    margin-bottom: 16px;
}
.hero-title .g1 { background: linear-gradient(90deg,#fff,#a78bfa,#f9a8d4); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.hero-title .g2 { background: linear-gradient(90deg,#67e8f9,#6ee7b7); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.hero-sub { font-size: 15px; color: #8892aa; max-width: 520px; line-height: 1.65; }

/* Multiselect pills */
[data-baseweb="tag"] {
    background: rgba(124,58,237,0.2) !important;
    border: 1px solid rgba(167,139,250,0.3) !important;
    border-radius: 100px !important;
}

[data-baseweb="tag"] span { color: #a78bfa !important; font-family: 'Space Mono', monospace !important; font-size: 11px !important; }

/* Selectbox & multiselect */
[data-baseweb="select"] { background: #12151c !important; border-color: rgba(255,255,255,0.1) !important; border-radius: 10px !important; }

/* Slider */
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] { background: #7c3aed !important; }

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #7c3aed, #ec4899) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
    padding: 8px 18px !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.35) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(124,58,237,0.08) !important;
    border: 1.5px dashed rgba(124,58,237,0.4) !important;
    border-radius: 12px !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.07) !important; }

/* Plotly charts bg */
.js-plotly-plot { background: transparent !important; }

/* Empty state */
.empty-state {
    padding: 44px 24px;
    text-align: center;
    border: 1.5px dashed rgba(255,255,255,0.07);
    border-radius: 14px;
    color: #4a5568;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_all():
    return load_data()

@st.cache_data(ttl=3600)
def get_freq():
    p = os.path.join("data","skill_frequency.csv")
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()

def last_updated():
    p = os.path.join("data","last_updated.txt")
    return open(p).read().strip() if os.path.exists(p) else "Unknown"

# Auto-run pipeline on first boot
if not os.path.exists(os.path.join("data","raw_jobs.csv")):
    from data_pipeline import run_pipeline
    from skill_extractor import process_all_jobs
    with st.spinner("🔄 Loading fresh job data... first boot takes ~60 seconds"):
        run_pipeline()
        process_all_jobs()
    st.cache_data.clear()

df         = load_all()
skill_freq = get_freq()

# ── SIDEBAR ───────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px'>
  <div style='width:40px;height:40px;border-radius:11px;background:linear-gradient(135deg,#7c3aed,#ec4899);display:grid;place-items:center;box-shadow:0 0 20px rgba(124,58,237,0.5)'>
    <span style='font-size:18px'>🎯</span>
  </div>
  <div>
    <div style='font-size:17px;font-weight:700;background:linear-gradient(90deg,#a78bfa,#f9a8d4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text'>Pathfinder</div>
    <div style='font-size:9px;color:#4a5568;letter-spacing:0.15em;text-transform:uppercase;font-family:Space Mono,monospace'>Job Navigator · 2026</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown('<div style="font-family:Space Mono,monospace;font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:#4a5568;margin-bottom:8px">Resume</div>', unsafe_allow_html=True)
uploaded = st.sidebar.file_uploader("Upload PDF or TXT", type=["pdf","txt"], label_visibility="collapsed")

auto_skills = []
if uploaded:
    with st.spinner("Reading resume..."):
        text = parse_pdf_resume(uploaded) if uploaded.type == "application/pdf" else parse_txt_resume(uploaded)
        if text:
            result = parse_resume_text(text)
            auto_skills = result["skills_found"]
            st.sidebar.success(f"✅ Found {len(auto_skills)} skills")
            st.sidebar.caption(f"Level: **{result['experience_level'].title()}**")
        else:
            st.sidebar.warning("Could not read resume. Add skills manually.")

st.sidebar.markdown("---")
st.sidebar.markdown('<div style="font-family:Space Mono,monospace;font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:#4a5568;margin-bottom:8px">Your Skills</div>', unsafe_allow_html=True)
user_skills = st.sidebar.multiselect(
    "Skills",
    options=sorted(ALL_SKILL_NAMES),
    default=sorted(list(set(auto_skills))) if auto_skills else ["python","sql"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown('<div style="font-family:Space Mono,monospace;font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:#4a5568;margin-bottom:8px">Target Market</div>', unsafe_allow_html=True)
target_country = st.sidebar.selectbox("Market", ["All","India","USA","Remote"], label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.markdown('<div style="font-family:Space Mono,monospace;font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:#4a5568;margin-bottom:8px">Filter</div>', unsafe_allow_html=True)
fresher_only = st.sidebar.checkbox("🟢 Show Fresher Friendly only", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style='font-family:Space Mono,monospace;font-size:10px;display:flex;flex-direction:column;gap:8px'>
  <div style='display:flex;justify-content:space-between'><span style='color:#4a5568'>STATUS</span><span style='color:#6ee7b7'>● Live</span></div>
  <div style='display:flex;justify-content:space-between'><span style='color:#4a5568'>JOBS</span><span style='color:#6ee7b7'>788 indexed</span></div>
  <div style='display:flex;justify-content:space-between'><span style='color:#4a5568'>SOURCE</span><span style='color:#a78bfa'>Adzuna + Jobicy</span></div>
  <div style='display:flex;justify-content:space-between'><span style='color:#4a5568'>UPDATED</span><span style='color:#8892aa'>{last_updated()}</span></div>
</div>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">
    <span class="g1">Find jobs you qualify for</span><br>
    <span class="g2">right now.</span>
  </div>
  <div class="hero-sub">Real-time data from 788 active job postings across India, USA & Remote. Select your skills — see exactly which jobs you can apply to today.</div>
</div>
""", unsafe_allow_html=True)

if not user_skills:
    st.markdown('<div class="empty-state">👈 Select your skills in the sidebar to get started.</div>', unsafe_allow_html=True)
    st.stop()

# ── FILTER ────────────────────────────────────────────────────────────
df_f = df[df["country"].isin([target_country,"Remote"])] if target_country != "All" else df.copy()
if fresher_only:
    df_f = df_f[df_f["experience_level"].isin(["fresher","unknown"])]

matched = get_jobs_unlocked(user_skills, df_f)
recs    = recommend_next_skill(user_skills, df_f)
sal     = get_salary_for_skills(user_skills, target_country)

# ── METRICS ───────────────────────────────────────────────────────────
st.markdown("<div style='padding:32px 48px 0'>", unsafe_allow_html=True)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Jobs You Qualify For", len(matched))
c2.metric("Skills You Have", len(user_skills))
c3.metric("Best Next Skill", recs[0]["skill"].title() if recs else "–", f"+{recs[0]['new_jobs_unlocked']} jobs" if recs else "")
c4.metric("Market", target_country)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='padding:32px 48px;display:flex;flex-direction:column;gap:48px'>", unsafe_allow_html=True)

# ── JOBS ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">✅ Jobs You Qualify For Right Now</div>', unsafe_allow_html=True)

if not matched:
    st.markdown('<div class="empty-state">No jobs matched. Try adding more skills or switching to All markets.</div>', unsafe_allow_html=True)
else:
    ca, cb = st.columns(2)
    min_match = ca.slider("Minimum match %", 40, 100, 60, step=10)
    show_n    = cb.selectbox("Show top", [10,25,50,100], index=1)
    visible   = [j for j in matched if j["match_score"] >= min_match][:show_n]

    EXP = {"fresher":("badge-fr","🟢 Fresher"),"junior":("badge-jr","🟡 Junior"),"mid":("badge-md","🟠 Mid"),"senior":("badge-sr","🔴 Senior")}
    CTR = {"India":("badge-in","🇮🇳 India"),"USA":("badge-us","🇺🇸 USA"),"Remote":("badge-re","🌐 Remote")}

    for job in visible:
        score    = job["match_score"]
        card_cls = "job-card" + ("" if score>=80 else " job-card-amber" if score>=60 else " job-card-rose")
        score_cls = "score-high" if score>=80 else "score-medium" if score>=60 else "score-low"
        ecls,elbl = EXP.get(job.get("experience_level","unknown"),("badge-uk","⚪ Open"))
        ccls,clbl = CTR.get(job["country"],("badge-re",job["country"]))
        matched_tags = "".join([f'<span class="badge badge-sc">{s}</span>' for s in job["matched_skills"]])
        missing_tags = "".join([f'<span class="badge badge-sm">{s}</span>' for s in job["missing_skills"]]) if job["missing_skills"] else '<span style="color:#6ee7b7;font-size:12px">✓ Perfect match</span>'

        st.markdown(f"""
        <div class="{card_cls}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div style="flex:1">
              <div style="margin-bottom:8px">
                <span class="badge {ccls}">{clbl}</span>
                <span class="badge {ecls}">{elbl}</span>
              </div>
              <div class="job-title">{job['title']}</div>
              <div class="job-meta">{job['company']}</div>
              <div>{matched_tags}{missing_tags}</div>
            </div>
            <div style="display:flex;flex-direction:column;align-items:flex-end;gap:10px;margin-left:16px">
              <div class="{score_cls}">{score}%</div>
              <a href="{job.get('url','#')}" target="_blank" style="font-family:Space Mono,monospace;font-size:10px;padding:7px 14px;background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff;border-radius:9px;text-decoration:none;box-shadow:0 2px 12px rgba(124,58,237,0.35)">Apply →</a>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── RECOMMENDATIONS ───────────────────────────────────────────────────
st.markdown('<div class="sec-header">🚀 What To Learn Next</div>', unsafe_allow_html=True)

if not recs:
    st.markdown('<div class="empty-state">You already qualify for all available jobs!</div>', unsafe_allow_html=True)
else:
    RC = ["rc1","rc2","rc3","rc4","rc5"]
    cols = st.columns(min(len(recs),5))
    for i,(rec,col) in enumerate(zip(recs,cols)):
        with col:
            st.markdown(f"""
            <div class="rec-card {RC[i]}">
              <div class="rec-num">+{rec['new_jobs_unlocked']}</div>
              <div class="rec-skill">{rec['skill']}</div>
              <div class="rec-tag">new jobs · {rec['total_jobs']} total</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── SALARY ────────────────────────────────────────────────────────────
st.markdown('<div class="sec-header">💰 Salary Insights</div>', unsafe_allow_html=True)

if sal.empty:
    msgs = {"Remote":"💡 Remote salaries aren't publicly listed. Switch to India or USA.",
            "All":"💡 Select India or USA to see salary data."}
    st.markdown(f'<div class="empty-state">{msgs.get(target_country,"💡 Add more skills like python or machine learning to see salary data.")}</div>', unsafe_allow_html=True)
else:
    sal_cols = st.columns(min(len(sal),4))
    for i,(_,row) in enumerate(sal.iterrows()):
        if i >= 4: break
        is_india = row["country"] == "India"
        with sal_cols[i]:
            st.markdown(f"""
            <div class="sal-card {'sal-india' if is_india else 'sal-usa'}">
              <div style="font-size:22px;margin-bottom:8px">{'🇮🇳' if is_india else '🇺🇸'}</div>
              <div class="sal-skill">{row['skill']}</div>
              <div class="{'sal-amount-india' if is_india else 'sal-amount-usa'}">{row['salary_formatted']}</div>
              <div class="sal-meta">{row['country']} · {int(row['job_count'])} jobs</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── MARKET COMPARISON ─────────────────────────────────────────────────
st.markdown('<div class="sec-header">🌍 India vs USA Skill Demand</div>', unsafe_allow_html=True)

gap_df = get_country_skill_gap(df)
c1, c2 = st.columns(2)

with c1:
    top = gap_df.nlargest(10,"india_count")[["skill","india_count"]]
    fig = px.bar(top, x="india_count", y="skill", orientation="h",
                 title="🇮🇳 Top Skills in India",
                 color="india_count", color_continuous_scale=["#ff6b00","#fcd34d"],
                 labels={"india_count":"Jobs","skill":"Skill"})
    fig.update_layout(yaxis=dict(autorange="reversed"),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#8892aa",family="Space Mono"),
                      title_font=dict(color="#f0f4ff",size=14),
                      showlegend=False, coloraxis_showscale=False,
                      margin=dict(l=0,r=0,t=40,b=0))
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    top = gap_df.nlargest(10,"usa_count")[["skill","usa_count"]]
    fig = px.bar(top, x="usa_count", y="skill", orientation="h",
                 title="🇺🇸 Top Skills in USA",
                 color="usa_count", color_continuous_scale=["#3b82f6","#a78bfa"],
                 labels={"usa_count":"Jobs","skill":"Skill"})
    fig.update_layout(yaxis=dict(autorange="reversed"),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#8892aa",family="Space Mono"),
                      title_font=dict(color="#f0f4ff",size=14),
                      showlegend=False, coloraxis_showscale=False,
                      margin=dict(l=0,r=0,t=40,b=0))
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── MARKET TRENDS ─────────────────────────────────────────────────────
st.markdown('<div class="sec-header">📊 Overall Market Trends</div>', unsafe_allow_html=True)

if not skill_freq.empty:
    fig = px.bar(skill_freq.head(25), x="count", y="skill", orientation="h",
                 title="Top 25 Most Demanded Skills",
                 color="count", color_continuous_scale=["#7c3aed","#ec4899","#06b6d4"],
                 labels={"count":"Jobs","skill":"Skill"})
    fig.update_layout(yaxis=dict(autorange="reversed"),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#8892aa",family="Space Mono"),
                      title_font=dict(color="#f0f4ff",size=14),
                      showlegend=False, coloraxis_showscale=False,
                      margin=dict(l=0,r=0,t=40,b=0), height=550)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"""
<div style='padding:20px 48px;border-top:1px solid rgba(255,255,255,0.07);font-family:Space Mono,monospace;font-size:10px;color:#4a5568;display:flex;justify-content:space-between'>
  <span>Pathfinder · Built for fresh graduates · India & USA</span>
  <span>Data: Adzuna + Jobicy · Updated: {last_updated()} · Refreshes every 24h</span>
</div>
""", unsafe_allow_html=True)