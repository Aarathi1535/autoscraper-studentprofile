import streamlit as st
import pandas as pd
import requests
from PIL import Image
import os

# Load student data (ensure roll_no is string in your CSV)
df = pd.read_csv('students.csv', dtype={'roll_no': str})

st.set_page_config(page_title="Student Performance Dashboard", layout="centered")
st.title("📊 Student Performance Dashboard")

roll = st.text_input("Enter Roll Number (e.g., 22A31A4402):").strip()

if roll:
    student = df[df['roll_no'] == roll]
    if not student.empty:
        data = student.iloc[0]

        # Display student image (image path from CSV or derived from roll number)
        image_path = f"student_images/{roll}.png"  # or .jpg if applicable
        if os.path.exists(image_path):
            img = Image.open(image_path)
            st.image(img, caption=f"{data['name']}'s Photo", use_container_width=True)
        else:
            st.info("📷 Image not found for this student.")

        # Show CGPA
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

        # HackerRank Badges
        st.markdown("### 🎖️ HackerRank Badges")
        if st.button("Fetch HackerRank Badges"):
            try:
                hr_username = data['hackerrank_url'].rstrip('/').split('/')[-1]
                api_url = f"https://www.hackerrank.com/rest/hackers/{hr_username}/profile"
                hr_res = requests.get(api_url)
                if hr_res.status_code == 200:
                    hr_data = hr_res.json()
                    badges = hr_data.get('badges', [])
                    if badges:
                        for badge in badges:
                            name = badge.get('name')
                            stars = badge.get('stars', {}).get('total', 0)
                            st.markdown(f"🌟 **{name}** - ⭐ {stars}")
                    else:
                        st.info("No badges found.")
                else:
                    st.error("Could not fetch HackerRank badges. Check username or profile visibility.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    else:
        st.error("❌ Roll number not found.")
