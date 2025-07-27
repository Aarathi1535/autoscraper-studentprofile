import streamlit as st
import pandas as pd
import requests

# Load student data
df = pd.read_csv('students.csv', dtype={'roll_no': str})

st.set_page_config(page_title="Student Performance Dashboard", layout="centered")
st.title("📊 Student Performance Dashboard")

roll = st.text_input("Enter Roll Number (e.g., 22A31A4402):").strip()

if roll:
    student = df[df['roll_no'] == roll]
    if not student.empty:
        data = student.iloc[0]

        st.subheader(f"🎓 CGPA: {data['cgpa']}")

        # SGPA Chart
        sgpa_cols = [col for col in df.columns if col.startswith('sem')]
        sgpa_values = [data[col] for col in sgpa_cols]
        sgpa_df = pd.DataFrame({'Semester': sgpa_cols, 'SGPA': sgpa_values})
        st.bar_chart(sgpa_df.set_index('Semester'))

        # LeetCode Stats
        st.markdown("### 🧠 LeetCode Stats")
        if st.button("Fetch LeetCode Stats"):
            username = data['leetcode_url'].rstrip('/').split('/')[-1]
            api_url = f"https://leetcode-stats-api.herokuapp.com/{username}"
            res = requests.get(api_url)
            if res.status_code == 200:
                stats = res.json()
                st.write(f"✅ Total Solved: {stats['totalSolved']}")
                st.write(f"⭐ Easy: {stats['easySolved']}, 🟠 Medium: {stats['mediumSolved']}, 🔴 Hard: {stats['hardSolved']}")
            else:
                st.error("Failed to fetch LeetCode stats.")

        # HackerRank Badge Image (Scraped as Image)
        st.markdown("### 🎖️ HackerRank Badges")
        if st.button("Show HackerRank Badges"):
            try:
                hr_username = data['hackerrank_url'].rstrip('/').split('/')[-1]
                badge_image_url = f"https://hackerrank-badges.vercel.app/{hr_username}"
                st.image(badge_image_url, caption=f"HackerRank Badges for {hr_username}", use_column_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    else:
        st.error("❌ Roll number not found.")
