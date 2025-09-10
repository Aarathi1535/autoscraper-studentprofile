import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import base64
from io import BytesIO

# ------------------------------
# Sidebar: File Upload
# ------------------------------
st.sidebar.subheader("Upload Student Data")
uploaded_file = st.sidebar.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

# Required columns for validation
REQUIRED_COLUMNS = ["Roll Number", "CGPA", "Backlogs","LeetCode URL", "HackerRank URL"]

@st.cache_data
def load_student_data(file):
    if file is not None:
        # Detect file type and read accordingly
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        elif file.name.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            st.error("Unsupported file type. Please upload CSV or Excel.")
            return None

        # Clean column names
        df.columns = df.columns.str.strip()

        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            st.error(f"Uploaded file is missing required columns: {', '.join(missing)}")
            return None

        return df
    return None

df = load_student_data(uploaded_file)

if df is None:
    st.warning("👆 Please upload a valid CSV or Excel file to continue.")
    st.stop()

# ------------------------------
# Helper Functions
# ------------------------------
def fetch_leetcode_data(profile_url):
    try:
        if not profile_url or pd.isna(profile_url):
            return {"LeetCode Rank": "N/A", "Problems Solved": "N/A"}

        response = requests.get(profile_url, timeout=5)
        if response.status_code != 200:
            return {"LeetCode Rank": "N/A", "Problems Solved": "N/A"}

        soup = BeautifulSoup(response.text, "html.parser")
        # Dummy parsing (customize for actual LeetCode HTML structure)
        rank = soup.find("div", class_="rank").text if soup.find("div", class_="rank") else "N/A"
        problems = soup.find("div", class_="solved-problems").text if soup.find("div", class_="solved-problems") else "N/A"

        return {"LeetCode Rank": rank, "Problems Solved": problems}
    except Exception:
        return {"LeetCode Rank": "N/A", "Problems Solved": "N/A"}

def fetch_hackerrank_data(profile_url):
    try:
        if not profile_url or pd.isna(profile_url):
            return {"Hackerrank Score": "N/A", "Badges": "N/A"}

        response = requests.get(profile_url, timeout=5)
        if response.status_code != 200:
            return {"Hackerrank Score": "N/A", "Badges": "N/A"}

        soup = BeautifulSoup(response.text, "html.parser")
        # Dummy parsing (customize for actual Hackerrank HTML structure)
        score = soup.find("div", class_="score").text if soup.find("div", class_="score") else "N/A"
        badges = soup.find("div", class_="badges").text if soup.find("div", class_="badges") else "N/A"

        return {"Hackerrank Score": score, "Badges": badges}
    except Exception:
        return {"Hackerrank Score": "N/A", "Badges": "N/A"}

def convert_df_to_excel(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

# ------------------------------
# App UI
# ------------------------------
st.title("📊 Student Profile Dashboard")

menu = ["Individual Student", "Bulk Data Download"]
choice = st.sidebar.selectbox("Navigation", menu)

# ------------------------------
# Individual Student
# ------------------------------
if choice == "Individual Student":
    st.subheader("🔍 Search Student by Roll Number")

    roll_number = st.text_input("Enter Roll Number")

    if st.button("Fetch Details"):
        if roll_number:
            student = df[df["Roll Number"].astype(str) == roll_number]

            if not student.empty:
                st.success("✅ Student Found!")

                cgpa = student["CGPA"].values[0]
                backlogs = student["Total Backlogs"].values[0]
                leetcode_url = student["Leet code links"].values[0]
                hackerrank_url = student["Hackerrank profile link"].values[0]

                # Fetch external data
                leetcode_data = fetch_leetcode_data(leetcode_url)
                hackerrank_data = fetch_hackerrank_data(hackerrank_url)

                # Display data
                st.write("### Student Details")
                st.write(f"**CGPA:** {cgpa}")
                st.write(f"**Total Backlogs:** {backlogs}")
                st.write(f"**LeetCode Profile:** {leetcode_url}")
                st.json(leetcode_data)
                st.write(f"**Hackerrank Profile:** {hackerrank_url}")
                st.json(hackerrank_data)
            else:
                st.error("❌ No student found with that Roll Number")
        else:
            st.warning("⚠️ Please enter a Roll Number")

# ------------------------------
# Bulk Data Download
# ------------------------------
elif choice == "Bulk Data Download":
    st.subheader("📥 Download Bulk Student Data with Coding Profiles")

    if st.button("Process and Download"):
        progress = st.progress(0)
        enriched_data = []

        for idx, row in df.iterrows():
            leetcode_data = fetch_leetcode_data(row["Leet code links"])
            hackerrank_data = fetch_hackerrank_data(row["Hackerrank profile link"])

            enriched_row = row.to_dict()
            enriched_row.update(leetcode_data)
            enriched_row.update(hackerrank_data)

            enriched_data.append(enriched_row)
            progress.progress((idx + 1) / len(df))

        enriched_df = pd.DataFrame(enriched_data)

        st.success("✅ Data processed successfully!")

        # Provide Excel download
        excel_data = convert_df_to_excel(enriched_df)
        st.download_button(
            label="📥 Download Excel File",
            data=excel_data,
            file_name="Enriched_Student_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


