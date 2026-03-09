import pandas as pd
import ast
from collections import defaultdict, Counter
import os

DATA_DIR          = "data"
JOBS_SKILLS_PATH  = os.path.join(DATA_DIR, "jobs_with_skills.csv")
SALARY_SKILL_PATH = os.path.join(DATA_DIR, "salary_by_skill.csv")


def load_data():
    df = pd.read_csv(JOBS_SKILLS_PATH)
    df["skills_found"] = df["skills_found"].apply(
        lambda x: ast.literal_eval(x)
        if isinstance(x, str) and x.startswith("[") else []
    )
    return df


def load_salary_data():
    path = SALARY_SKILL_PATH
    if not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_csv(path)


def get_jobs_unlocked(user_skills, df, match_threshold=0.4):
    user_skills_set = set(s.lower() for s in user_skills)
    matched_jobs = []

    for _, row in df.iterrows():
        job_skills = set(row["skills_found"])
        if not job_skills:
            continue
        overlap     = user_skills_set & job_skills
        match_score = len(overlap) / len(job_skills)
        if match_score >= match_threshold:
            matched_jobs.append({
                "title":          row["title"],
                "company":        row["company"],
                "country":        row["country"],
                "match_score":    round(match_score * 100),
                "matched_skills": list(overlap),
                "missing_skills": list(job_skills - user_skills_set),
                "salary_min":     row.get("salary_min", None),
                "salary_max":     row.get("salary_max", None),
                "url":            row.get("url", ""),
                "experience_level": row.get("experience_level", "unknown"),
                "source":         row.get("source", "")
            })

    matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    return matched_jobs


def recommend_next_skill(user_skills, df, top_n=5):
    user_skills_set = set(s.lower() for s in user_skills)
    current_jobs    = len(get_jobs_unlocked(user_skills, df))

    all_skills  = []
    for skills in df["skills_found"]:
        all_skills.extend(skills)
    skill_pool = set(all_skills) - user_skills_set

    skill_impact = []
    for skill in skill_pool:
        new_skills = user_skills_set | {skill}
        new_jobs   = len(get_jobs_unlocked(list(new_skills), df))
        impact     = new_jobs - current_jobs
        if impact > 0:
            skill_impact.append({
                "skill":             skill,
                "new_jobs_unlocked": impact,
                "total_jobs":        new_jobs
            })

    skill_impact.sort(key=lambda x: x["new_jobs_unlocked"], reverse=True)
    return skill_impact[:top_n]


def get_country_skill_gap(df):
    india_skills = Counter()
    usa_skills   = Counter()

    for _, row in df.iterrows():
        if row["country"] == "India":
            india_skills.update(row["skills_found"])
        elif row["country"] == "USA":
            usa_skills.update(row["skills_found"])

    all_skills = set(list(india_skills.keys()) + list(usa_skills.keys()))
    gap = []
    for skill in all_skills:
        i = india_skills.get(skill, 0)
        u = usa_skills.get(skill, 0)
        if i + u > 3:
            gap.append({
                "skill":       skill,
                "india_count": i,
                "usa_count":   u,
                "gap":         i - u
            })

    return pd.DataFrame(gap).sort_values("gap", ascending=False)


def get_salary_for_skills(user_skills, country="All"):
    sal_df = load_salary_data()
    if sal_df.empty:
        return pd.DataFrame()

    result = sal_df[sal_df["skill"].isin(user_skills)]
    if country != "All":
        result = result[result["country"] == country]

    return result.sort_values("avg_salary", ascending=False)


def run_recommendation(user_skills, target_country="All"):
    print(f"\nAnalyzing: {user_skills} | Market: {target_country}")
    print("=" * 55)

    df = load_data()

    if target_country != "All":
        df_filtered = df[df["country"].isin([target_country, "Remote"])]
    else:
        df_filtered = df

    # Jobs matched
    matched_jobs = get_jobs_unlocked(user_skills, df_filtered)
    print(f"\nJobs you qualify for RIGHT NOW: {len(matched_jobs)}")
    for job in matched_jobs[:5]:
        print(f"  [{job['match_score']}%] {job['title']} @ {job['company']} ({job['country']})")
        print(f"    Missing: {job['missing_skills']}")
        if job["url"]:
            print(f"    Apply: {job['url']}")

    # Next skill
    recommendations = recommend_next_skill(user_skills, df_filtered)
    print(f"\nTop skills to learn NEXT:")
    for rec in recommendations:
        print(f"  '{rec['skill']}' → +{rec['new_jobs_unlocked']} jobs (total: {rec['total_jobs']})")

    # Salary for current skills
    salary_info = get_salary_for_skills(user_skills, target_country)
    if not salary_info.empty:
        print(f"\nSalary ranges for your skills:")
        for _, row in salary_info.iterrows():
            print(f"  {row['skill']} ({row['country']}): {row['salary_formatted']} avg — {int(row['job_count'])} jobs")

    # Country gap
    gap_df = get_country_skill_gap(df)
    print(f"\nIndia vs USA skill gap (top 10):")
    print(gap_df.head(10).to_string(index=False))

    return matched_jobs, recommendations, gap_df


if __name__ == "__main__":
    test_skills = ["python", "sql", "machine learning"]
    run_recommendation(test_skills, target_country="India")
    print("\n")
    run_recommendation(test_skills, target_country="USA")