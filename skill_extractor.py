import pandas as pd
import re
from collections import Counter
import os

DATA_DIR           = "data"
RAW_JOBS_PATH      = os.path.join(DATA_DIR, "raw_jobs.csv")
JOBS_SKILLS_PATH   = os.path.join(DATA_DIR, "jobs_with_skills.csv")
SKILL_FREQ_PATH    = os.path.join(DATA_DIR, "skill_frequency.csv")
SALARY_SKILL_PATH  = os.path.join(DATA_DIR, "salary_by_skill.csv")

SKILLS = {
    "python":                 ["python"],
    "r":                      [r"\br\b", "r programming"],
    "sql":                    ["sql"],
    "java":                   [r"\bjava\b"],
    "scala":                  ["scala"],
    "javascript":             ["javascript", r"\bjs\b"],
    "typescript":             ["typescript", r"\bts\b"],
    "c++":                    [r"c\+\+", "cpp"],
    "c#":                     [r"c#", "csharp"],
    "go":                     [r"\bgolang\b", r"\bgo\b"],
    "rust":                   [r"\brust\b"],
    "bash":                   ["bash", "shell scripting"],
    "swift":                  ["swift"],
    "kotlin":                 ["kotlin"],
    "machine learning":       ["machine learning", r"\bml\b"],
    "deep learning":          ["deep learning", r"\bdl\b"],
    "nlp":                    ["nlp", "natural language processing"],
    "computer vision":        ["computer vision", r"\bcv\b"],
    "time series":            ["time series", "time-series"],
    "statistics":             ["statistics", "statistical"],
    "data analysis":          ["data analysis", "data analytics", "analytical"],
    "data wrangling":         ["data wrangling", "data cleaning", "data preprocessing"],
    "feature engineering":    ["feature engineering"],
    "model deployment":       ["model deployment", "model serving"],
    "a/b testing":            ["a/b testing", "ab testing", "experimentation"],
    "reinforcement learning": ["reinforcement learning", r"\brl\b"],
    "generative ai":          ["generative ai", "genai", r"\bllm\b", "large language model"],
    "pandas":                 ["pandas"],
    "numpy":                  ["numpy"],
    "scikit-learn":           ["scikit-learn", "sklearn"],
    "xgboost":                ["xgboost"],
    "lightgbm":               ["lightgbm"],
    "tensorflow":             ["tensorflow", r"\btf\b"],
    "keras":                  ["keras"],
    "pytorch":                ["pytorch", "torch"],
    "huggingface":            ["huggingface", "hugging face", "transformers"],
    "opencv":                 ["opencv"],
    "nltk":                   ["nltk"],
    "spacy":                  ["spacy"],
    "fastapi":                ["fastapi", "fast api"],
    "flask":                  ["flask"],
    "django":                 ["django"],
    "streamlit":              ["streamlit"],
    "spark":                  ["apache spark", r"\bspark\b"],
    "hadoop":                 ["hadoop"],
    "kafka":                  ["kafka"],
    "airflow":                ["airflow"],
    "dbt":                    [r"\bdbt\b"],
    "etl":                    [r"\betl\b", "data pipeline"],
    "data warehouse":         ["data warehouse", "data warehousing"],
    "data lake":              ["data lake"],
    "aws":                    [r"\baws\b", "amazon web services"],
    "azure":                  ["azure"],
    "gcp":                    [r"\bgcp\b", "google cloud"],
    "docker":                 ["docker"],
    "kubernetes":             ["kubernetes", r"\bk8s\b"],
    "mlflow":                 ["mlflow"],
    "mlops":                  ["mlops"],
    "ci/cd":                  ["ci/cd", "cicd", "continuous integration"],
    "git":                    [r"\bgit\b"],
    "github":                 ["github"],
    "linux":                  ["linux", "unix"],
    "mysql":                  ["mysql"],
    "postgresql":             ["postgresql", "postgres"],
    "mongodb":                ["mongodb", "mongo"],
    "redis":                  ["redis"],
    "elasticsearch":          ["elasticsearch"],
    "bigquery":               ["bigquery"],
    "snowflake":              ["snowflake"],
    "databricks":             ["databricks"],
    "tableau":                ["tableau"],
    "power bi":               ["power bi", "powerbi"],
    "matplotlib":             ["matplotlib"],
    "seaborn":                ["seaborn"],
    "plotly":                 ["plotly"],
    "looker":                 ["looker"],
    "communication":          ["communication", "communicating"],
    "teamwork":               ["teamwork", "team player", "collaboration", "collaborative"],
    "problem solving":        ["problem solving", "problem-solving", "analytical thinking"],
    "leadership":             ["leadership", "leading", "lead a team"],
    "project management":     ["project management", "pmp"],
    "agile":                  ["agile", "scrum", "kanban"],
    "scrum":                  ["scrum"]
}

ALL_SKILL_NAMES = sorted(SKILLS.keys())


def extract_skills(text):
    if not text or len(str(text).strip()) < 20:
        return []
    text_lower = str(text).lower()
    found = []
    for skill_name, patterns in SKILLS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found.append(skill_name)
                break
    return list(set(found))


def build_salary_insights(df):
    rows = []
    for _, job in df.iterrows():
        sal_min = job.get("salary_min")
        sal_max = job.get("salary_max")
        country = job.get("country")
        skills  = job.get("skills_found", [])

        if not skills:
            continue
        if pd.isna(sal_min) and pd.isna(sal_max):
            continue

        avg_sal = None
        if not pd.isna(sal_min) and not pd.isna(sal_max):
            avg_sal = (float(sal_min) + float(sal_max)) / 2
        elif not pd.isna(sal_min):
            avg_sal = float(sal_min)
        elif not pd.isna(sal_max):
            avg_sal = float(sal_max)

        if country == "India" and avg_sal and avg_sal > 10000:
            currency = "INR"
            symbol   = "₹"
        elif country == "USA" and avg_sal and avg_sal > 1000:
            currency = "USD"
            symbol   = "$"
        else:
            continue

        for skill in skills:
            rows.append({
                "skill":    skill,
                "country":  country,
                "currency": currency,
                "symbol":   symbol,
                "salary":   avg_sal
            })

    if not rows:
        return pd.DataFrame()

    sal_df = pd.DataFrame(rows)
    salary_summary = sal_df.groupby(
        ["skill", "country", "currency", "symbol"]
    )["salary"].agg(
        avg_salary="mean",
        job_count="count"
    ).reset_index()

    salary_summary["avg_salary"] = salary_summary["avg_salary"].round(0)
    salary_summary["salary_formatted"] = salary_summary.apply(
        lambda r: f"{r['symbol']}{int(r['avg_salary']):,}", axis=1
    )
    salary_summary = salary_summary[salary_summary["job_count"] >= 2]
    salary_summary.sort_values("avg_salary", ascending=False, inplace=True)
    return salary_summary

def extract_experience_level(text):
    if not text:
        return "unknown"
    text_lower = str(text).lower()

    if any(x in text_lower for x in [
        "fresher", "fresh graduate", "0 years", "no experience required",
        "entry level", "entry-level", "0-1 year", "recent graduate",
        "new graduate", "campus hire", "trainee", "intern"
    ]):
        return "fresher"

    patterns = [
        r'(\d+)\+?\s*-?\s*(\d+)?\s*years?\s*of\s*(relevant\s*)?experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'minimum\s*(\d+)\+?\s*years?',
        r'at\s*least\s*(\d+)\+?\s*years?',
        r'(\d+)\+\s*years?',
    ]

    years = None
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            years = int(match.group(1))
            break

    if years is None:
        return "unknown"
    elif years <= 1:
        return "fresher"
    elif years <= 3:
        return "junior"
    elif years <= 6:
        return "mid"
    else:
        return "senior"


def process_all_jobs():
    print("=" * 55)
    print("SKILL EXTRACTOR")
    print("=" * 55)

    print(f"Loading jobs from {RAW_JOBS_PATH}...")
    df = pd.read_csv(RAW_JOBS_PATH)
    print(f"Loaded {len(df)} jobs")

    print("Extracting skills from descriptions...")
    df["skills_found"] = df["description"].apply(extract_skills)
    df["skill_count"]  = df["skills_found"].apply(len)
    df["experience_level"] = df["description"].apply(extract_experience_level)

    df.to_csv(JOBS_SKILLS_PATH, index=False)

    all_skills = []
    for skills in df["skills_found"]:
        all_skills.extend(skills)
    skill_freq = Counter(all_skills)
    skill_df = pd.DataFrame(
        skill_freq.most_common(60),
        columns=["skill", "count"]
    )
    skill_df.to_csv(SKILL_FREQ_PATH, index=False)

    salary_df = build_salary_insights(df)
    if not salary_df.empty:
        salary_df.to_csv(SALARY_SKILL_PATH, index=False)
        print(f"Salary data built for {len(salary_df)} skill/country combinations")

    print(f"\nTop 20 skills (overall):")
    print(skill_df.head(20).to_string(index=False))

    print(f"\nTop 10 skills — India:")
    india = []
    for s in df[df["country"] == "India"]["skills_found"]:
        india.extend(s)
    for skill, count in Counter(india).most_common(10):
        print(f"  {skill}: {count}")

    print(f"\nTop 10 skills — USA:")
    usa = []
    for s in df[df["country"] == "USA"]["skills_found"]:
        usa.extend(s)
    for skill, count in Counter(usa).most_common(10):
        print(f"  {skill}: {count}")

    matched = (df["skill_count"] > 0).sum()
    print(f"\nJobs with skills found: {matched}/{len(df)} ({round(matched/len(df)*100)}%)")
    print(f"Average skills per job: {df['skill_count'].mean():.1f}")

    if not salary_df.empty:
        print(f"\nTop 10 highest paying skills:")
        print(salary_df.head(10).to_string(index=False))

    return df, skill_df, salary_df


if __name__ == "__main__":
    process_all_jobs()

def extract_experience_level(text):
    """
    Detect required experience level from job description.
    Returns: 'fresher', 'junior', 'mid', 'senior'
    """
    if not text:
        return "unknown"
    text_lower = str(text).lower()

    # Explicit fresher signals
    if any(x in text_lower for x in [
        "fresher", "fresh graduate", "0 years", "no experience required",
        "entry level", "entry-level", "0-1 year", "recent graduate",
        "new graduate", "campus hire", "trainee", "intern"
    ]):
        return "fresher"

    # Look for year patterns
    patterns = [
        r'(\d+)\+?\s*-?\s*(\d+)?\s*years?\s*of\s*(relevant\s*)?experience',
        r'(\d+)\+?\s*years?\s*experience',
        r'minimum\s*(\d+)\+?\s*years?',
        r'at\s*least\s*(\d+)\+?\s*years?',
        r'(\d+)\+\s*years?',
    ]

    years = None
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            years = int(match.group(1))
            break

    if years is None:
        return "unknown"
    elif years <= 1:
        return "fresher"
    elif years <= 3:
        return "junior"
    elif years <= 6:
        return "mid"
    else:
        return "senior"