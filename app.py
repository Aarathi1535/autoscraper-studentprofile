import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json
from io import BytesIO
import base64
import time
import re
from bs4 import BeautifulSoup

# Set page config as the very first Streamlit command
st.set_page_config(page_title="Student Performance Dashboard", layout="wide")

def fetch_hackerrank_badges_svg(username):
    """
    Fetch HackerRank badges by parsing SVG structure directly
    Returns list of dictionaries with badge names and star counts
    """
    # Predefined list of valid HackerRank badges
    VALID_HACKERRANK_BADGES = {
        'Problem Solving', 'Java', 'Python', 'C Language', 'Cpp', 'C#', 'JavaScript',
        'Sql', '30 Days of Code', '10 Days of JavaScript', '10 Days of Statistics',
        'Algorithms', 'Data Structures', 'Regex', 'Artificial Intelligence',
        'Databases', 'Shell', 'Linux Shell', 'Functional Programming',
        'Mathematics', 'Days of ML', 'Rust', 'Kotlin', 'Swift', 'Scala',
        'Ruby', 'Go', 'Statistics', 'Interview Preparation Kit',
        'Object Oriented Programming', 'Linux Shell', 'Security'
    }
    try:
        badge_url = f'https://hackerrank-badges.vercel.app/{username}'
        response = requests.get(badge_url, timeout=15)
        if response.status_code == 200:
            svg_xml = response.text
            soup = BeautifulSoup(svg_xml, 'xml')
            
            # Look for badge information in the SVG
            text_elements = soup.find_all('text')
            
            # Look for star sections - this is the key structure
            star_sections = soup.find_all('g', class_='star-section')
            
            # Look for individual badge stars
            badge_stars = soup.find_all('svg', class_='badge-star')
            
            # Display all text content to understand the structure
            all_texts = []
            for text in text_elements:
                text_content = text.get_text().strip()
                if text_content and len(text_content) > 1:
                    all_texts.append(text_content)
            
            # Analyze star sections
            for i, star_section in enumerate(star_sections):
                stars_in_section = star_section.find_all('svg', class_='badge-star')
            
            # Try to identify actual badges by looking for meaningful patterns
            badge_keywords = ['java', 'python', 'sql', 'javascript', 'cpp', 'problem solving', 
                            'algorithms', 'data structures', '30 days', '10 days', 'ruby', 
                            'swift', 'golang', 'rust', 'kotlin', 'scala', 'c', 'shell',
                            'functional programming', 'object oriented programming']
            
            real_badges = []
            
            # Strategy: Match badges with their corresponding star sections
            # The structure seems to be: badge text + associated star-section
            for text in all_texts:
                text_lower = text.lower()
                for keyword in badge_keywords:
                    if keyword in text_lower:
                        # ✅ Check if badge is in VALID_HACKERRANK_BADGES
                        text_title = text.strip().title()
                        if text_title not in VALID_HACKERRANK_BADGES:
                            continue  # Skip if not a valid badge name
                        
                        # Find the text element in the soup
                        text_elem = None
                        for elem in text_elements:
                            if elem.get_text().strip().lower() == text_lower:
                                text_elem = elem
                                break
                        
                        stars = 0
                        if text_elem:
                            # Strategy 1: Look for star-section in the same parent or nearby elements
                            # Traverse up the DOM tree to find associated star sections
                            current = text_elem
                            found_stars = False
                            
                            # Check multiple levels up the DOM tree
                            for level in range(5):  # Check up to 5 levels up
                                if current is None:
                                    break
                                    
                                # Look for star-section in current element
                                star_section = current.find('g', class_='star-section')
                                if star_section:
                                    badge_star_elements = star_section.find_all('svg', class_='badge-star')
                                    stars = len(badge_star_elements)
                                    found_stars = True
                                    break
                                
                                # Look for star-section in siblings
                                if current.parent:
                                    sibling_star_sections = current.parent.find_all('g', class_='star-section')
                                    if sibling_star_sections:
                                        # Take the first star section found (assuming it's related)
                                        badge_star_elements = sibling_star_sections[0].find_all('svg', class_='badge-star')
                                        stars = len(badge_star_elements)
                                        found_stars = True
                                        break
                                
                                current = current.parent
                            
                            # Strategy 2: If no direct association found, try positional matching
                            if not found_stars and star_sections:
                                # Get text position
                                text_x = text_elem.get('x', '0')
                                text_y = text_elem.get('y', '0')
                                
                                try:
                                    text_x_num = float(text_x) if str(text_x).replace('.', '').replace('-', '').isdigit() else 0
                                    text_y_num = float(text_y) if str(text_y).replace('.', '').replace('-', '').isdigit() else 0
                                    
                                    closest_star_section = None
                                    min_distance = float('inf')
                                    
                                    for star_section in star_sections:
                                        # Get star section position from transform attribute
                                        transform = star_section.get('transform', '')
                                        if 'translate' in transform:
                                            # Extract translate values
                                            translate_match = re.search(r'translate\(([^,]+),\s*([^)]+)\)', transform)
                                            if translate_match:
                                                try:
                                                    star_x = float(translate_match.group(1))
                                                    star_y = float(translate_match.group(2))
                                                    
                                                    distance = ((star_x - text_x_num) ** 2 + (star_y - text_y_num) ** 2) ** 0.5
                                                    if distance < min_distance:
                                                        min_distance = distance
                                                        closest_star_section = star_section
                                                except:
                                                    continue
                                    
                                    if closest_star_section:
                                        badge_star_elements = closest_star_section.find_all('svg', class_='badge-star')
                                        stars = len(badge_star_elements)
                                        found_stars = True
                                        
                                except:
                                    pass
                            
                            # Strategy 3: Simple distribution if we have star sections
                            if not found_stars and star_sections:
                                st.write("  📊 Using simple distribution strategy...")
                                # Count total stars and distribute among badges
                                total_star_elements = soup.find_all('svg', class_='badge-star')
                                total_badges = len([t for t in all_texts if any(kw in t.lower() for kw in badge_keywords)])
                                if total_badges > 0:
                                    stars = len(total_star_elements) // total_badges
                                    st.write(f"  ⭐ Estimated {stars} stars ({len(total_star_elements)} total / {total_badges} badges)")
                        
                        real_badges.append({
                            'Badge Name': text.title(),
                            'Stars': stars
                        })
                        
                        break  # Found this badge, don't check other keywords
            
            # Remove duplicates
            seen = set()
            unique_badges = []
            for badge in real_badges:
                badge_key = badge['Badge Name'].lower()
                if badge_key not in seen:
                    seen.add(badge_key)
                    unique_badges.append(badge)
            
            return unique_badges if unique_badges else None
            
        else:
            st.write(f"HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        st.write(f"Exception occurred: {str(e)}")
        return None

# Load student data
@st.cache_data
def load_student_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    # Clean column names
    df.columns = df.columns.str.strip()
    return df

st.title("📊 Student Performance Dashboard")
st.header("📁 Upload Student Data")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a CSV file", 
    type="csv",
    help="Upload a CSV file containing student data with required columns"
)

# Check if file is uploaded before proceeding
if uploaded_file is not None:
    df = load_student_data(uploaded_file)
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    option = st.sidebar.selectbox("Choose Option", ["Individual Student", "Bulk Data Download"])

    if option == "Individual Student":
        st.header("Individual Student Analysis")
        
        roll = st.text_input("Enter Roll Number (e.g., 23A31A4401):").strip().upper()
        if roll:
            student = df[df['Roll Number'].str.upper() == roll]
            if not student.empty:
                data = student.iloc[0]
                # Display basic info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("🎓 CGPA", f"{data['CGPA']}")
                with col2:
                    st.metric("📚 Total Backlogs", f"{data['Total Backlogs']}")
                with col3:
                    st.metric("📋 Roll Number", data['Roll Number'])
                
                # Create tabs for different sections
                tab1, tab2, tab3 = st.tabs(["🧠 LeetCode Stats", "🎖️ HackerRank Stats", "📊 Performance Summary"])
                
                with tab1:
                    st.markdown("### 🧠 LeetCode Statistics")
                    leetcode_url = data['LeetCode profile']
                    
                    if pd.notna(leetcode_url) and leetcode_url != '' and 'leetcode.com' in str(leetcode_url):
                        if st.button("Fetch LeetCode Stats", key="leetcode_btn"):
                            with st.spinner("Fetching LeetCode data..."):
                                try:
                                    # Extract username from URL
                                    username = str(leetcode_url).rstrip('/').split('/')[-1]
                                    if username in ['profile', 'account', 'login', '']:
                                        # Try to extract username from URL path
                                        url_parts = str(leetcode_url).split('/')
                                        username = next((part for part in url_parts if part.startswith('u/') or part.startswith('profile/')), '').replace('u/', '').replace('profile/', '')
                                    
                                    if username:
                                        # LeetCode Stats API
                                        stats_api_url = f"https://leetcode-stats-api.herokuapp.com/{username}"
                                        stats_response = requests.get(stats_api_url, timeout=10)
                                        
                                        if stats_response.status_code == 200:
                                            stats = stats_response.json()
                                            
                                            # Display basic stats
                                            col1, col2, col3, col4 = st.columns(4)
                                            with col1:
                                                st.metric("✅ Total Solved", stats.get('totalSolved', 0))
                                            with col2:
                                                st.metric("⭐ Easy Problems", stats.get('easySolved', 0))
                                            with col3:
                                                st.metric("🟠 Medium Problems", stats.get('mediumSolved', 0))
                                            with col4:
                                                st.metric("🔴 Hard Problems", stats.get('hardSolved', 0))
                                            
                                            # Additional stats if available
                                            if 'acceptanceRate' in stats:
                                                st.metric("📈 Acceptance Rate", f"{stats['acceptanceRate']:.1f}%")
                                            if 'ranking' in stats:
                                                st.metric("🏆 Ranking", stats['ranking'])
                                        
                                        # Try to fetch submission timeline (Alternative API)
                                        st.markdown("#### 📅 Recent Activity Timeline")
                                        try:
                                            # GraphQL query for LeetCode submissions
                                            graphql_url = "https://leetcode.com/graphql"
                                            query = """
                                            query recentSubmissions($username: String!) {
                                                recentSubmissionList(username: $username) {
                                                    title
                                                    titleSlug
                                                    timestamp
                                                    statusDisplay
                                                    lang
                                                }
                                            }
                                            """
                                            
                                            headers = {
                                                'Content-Type': 'application/json',
                                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                            }
                                            
                                            response = requests.post(
                                                graphql_url, 
                                                json={'query': query, 'variables': {'username': username}}, 
                                                headers=headers,
                                                timeout=10
                                            )
                                            
                                            if response.status_code == 200:
                                                submission_data = response.json()
                                                submissions = submission_data.get('data', {}).get('recentSubmissionList', [])
                                                
                                                if submissions:
                                                    # Create DataFrame for submissions
                                                    df_submissions = pd.DataFrame(submissions[:10])  # Show last 10 submissions
                                                    df_submissions['timestamp'] = pd.to_datetime(df_submissions['timestamp'], unit='s')
                                                    df_submissions['date'] = df_submissions['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
                                                    
                                                    st.dataframe(
                                                        df_submissions[['title', 'statusDisplay', 'lang', 'date']], 
                                                        use_container_width=True
                                                    )
                                                else:
                                                    st.info("No recent submissions found or profile is private.")
                                            else:
                                                st.warning("Could not fetch submission timeline. Profile might be private.")
                                        
                                        except Exception as e:
                                            st.warning(f"Timeline fetch failed: Could not retrieve submission history")
                                        
                                    else:
                                        st.error("Could not extract username from LeetCode URL")
                                
                                except requests.exceptions.RequestException:
                                    st.error("Failed to fetch LeetCode stats. Please check the URL or try again later.")
                                except Exception as e:
                                    st.error(f"An error occurred: {str(e)}")
                    else:
                        st.warning("No valid LeetCode URL found for this student.")
                
                with tab2:
                    st.markdown("### 🎖️ HackerRank Statistics")
                    hackerrank_url = data['Hackerrank profile']
                    
                    if pd.notna(hackerrank_url) and hackerrank_url != '' and 'hackerrank.com' in str(hackerrank_url):
                        if st.button("Fetch HackerRank Stats", key="hackerrank_btn"):
                            with st.spinner("Fetching HackerRank data..."):
                                try:
                                    # Extract username from URL
                                    username = str(hackerrank_url).rstrip('/').split('/')[-1]
                                    
                                    # Display the badge image first
                                    badge_image_url = f"https://hackerrank-badges.vercel.app/{username}"
                                    st.image(badge_image_url, caption=f"HackerRank Badges for {username}", use_column_width=True)
                                    
                                    # Use the new SVG parsing function
                                    st.markdown("#### 🏆 Badge Details")
                                    
                                    badges = fetch_hackerrank_badges_svg(username)
                                    
                                    if badges:
                                        st.success(f"✅ Successfully extracted {len(badges)} badges!")
                                        
                                        # Create DataFrame for better display
                                        badges_df = pd.DataFrame(badges)
                                        
                                        # Display badges in a nice format
                                        st.dataframe(badges_df, use_container_width=True)
                                        
                                        # Show summary statistics
                                        total_badges = len(badges)
                                        total_stars = sum(badge['Stars'] for badge in badges if isinstance(badge['Stars'], int))
                                        avg_stars = total_stars / total_badges if total_badges > 0 else 0
                                        
                                        # Display summary metrics
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("🎖️ Total Badges", total_badges)
                                        with col2:
                                            st.metric("⭐ Total Stars", total_stars)
                                        
                                        # Show badges grouped by star count
                                        st.markdown("#### ⭐ Badges by Star Rating")
                                        star_groups = {}
                                        for badge in badges:
                                            stars = badge['Stars']
                                            if isinstance(stars, int):
                                                if stars not in star_groups:
                                                    star_groups[stars] = []
                                                star_groups[stars].append(badge['Badge Name'])
                                        
                                        for stars in sorted(star_groups.keys(), reverse=True):
                                            badge_names = ", ".join(star_groups[stars])
                                            star_emoji = "⭐" * stars if stars > 0 else "⚪"
                                            st.write(f"{star_emoji} **{stars} Star{'s' if stars != 1 else ''}:** {badge_names}")
                                        
                                        # Export badges data
                                        st.markdown("#### 📥 Export Badge Data")
                                        badges_json = json.dumps(badges, indent=2)
                                        st.download_button(
                                            label="Download Badge Data as JSON",
                                            data=badges_json,
                                            file_name=f"hackerrank_badges_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                            mime="application/json"
                                        )
                                        
                                    else:
                                        st.warning("⚠️ Could not extract badge information from the SVG.")
                                        
                                        # Provide manual entry option
                                        st.markdown("### ✏️ Manual Badge Entry")
                                        st.info("Since automatic extraction failed, you can manually enter badge information by looking at the image above.")
                                        
                                        with st.form(f"manual_badges_{username}"):
                                            st.markdown("**Enter badge information manually:**")
                                            
                                            num_badges = st.number_input("How many badges do you see?", min_value=0, max_value=20, value=0)
                                            
                                            manual_badges = []
                                            if num_badges > 0:
                                                for i in range(num_badges):
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        badge_name = st.text_input(f"Badge {i+1} Name:", key=f"name_{i}")
                                                    with col2:
                                                        badge_stars = st.number_input(f"Badge {i+1} Stars:", min_value=0, max_value=5, value=0, key=f"stars_{i}")
                                                    
                                                    if badge_name:
                                                        manual_badges.append({"Badge Name": badge_name, "Stars": badge_stars})
                                            
                                            submitted = st.form_submit_button("💾 Save Manual Badges")
                                            
                                            if submitted and manual_badges:
                                                st.success(f"✅ Manually entered {len(manual_badges)} badges!")
                                                manual_df = pd.DataFrame(manual_badges)
                                                st.dataframe(manual_df, use_container_width=True)
                                                
                                                # Show summary for manual badges
                                                total_manual_stars = sum(badge['Stars'] for badge in manual_badges)
                                                st.metric("Total Manual Stars", total_manual_stars)
                                        
                                        # Show troubleshooting tips
                                        with st.expander("🔧 Troubleshooting Tips"):
                                            st.markdown("""
                                            **Common issues and solutions:**
                                            
                                            1. **Profile is Private**: Make sure the HackerRank profile is public
                                            2. **Username Issue**: Check if the username extracted from URL is correct
                                            3. **No Badges**: User might not have earned any badges yet
                                            4. **Server Issue**: The badge service might be temporarily down
                                            5. **SVG Structure Changed**: The badge generator might have updated its format
                                            
                                            **What you can do:**
                                            - Enable debug mode above to see the raw SVG structure
                                            - Try accessing the URL directly: `https://hackerrank-badges.vercel.app/{username}`
                                            - Use manual entry if automatic parsing fails
                                            """)
                                    
                                except requests.exceptions.RequestException:
                                    st.error("Failed to fetch HackerRank data. Please check the URL or try again later.")
                                except Exception as e:
                                    st.error(f"An error occurred: {str(e)}")
                                    
                                    # Show error details in debug mode
                                    if st.checkbox("Show error details", key=f"error_debug_{username}"):
                                        st.code(str(e))
                    else:
                        st.warning("No valid HackerRank URL found for this student.")
                
                with tab3:
                    st.markdown("### 📊 Performance Summary")
                    
                    # Performance metrics
                    cgpa_status = "Excellent" if data['CGPA'] >= 9.0 else "Good" if data['CGPA'] >= 8.0 else "Average" if data['CGPA'] >= 7.0 else "Below Average"
                    backlog_status = "No Backlogs" if data['Total Backlogs'] == 0 else f"{data['Total Backlogs']} Backlog(s)"
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**CGPA Status:** {cgpa_status}")
                        st.info(f"**Backlog Status:** {backlog_status}")
                    with col2:
                        st.info(f"**HackerRank Profile:** {'✅ Available' if pd.notna(data['Hackerrank profile link']) else '❌ Not Available'}")
                        st.info(f"**LeetCode Profile:** {'✅ Available' if pd.notna(data['Leet code links']) else '❌ Not Available'}")
            else:
                st.error("❌ Roll number not found.")
    
    elif option == "Bulk Data Download":
        st.header("Bulk Data Download")
        
        st.markdown("Download comprehensive data for all students including LeetCode and HackerRank statistics.")
        
        if st.button("📥 Generate and Download Student Data", key="bulk_download"):
            with st.spinner("Fetching data for all students... This may take a while..."):
                
                # Create a copy of the original dataframe
                enhanced_df = df.copy()
                
                # Add new columns for enhanced data
                enhanced_df['LeetCode_Total_Solved'] = ''
                enhanced_df['LeetCode_Easy_Solved'] = ''
                enhanced_df['LeetCode_Medium_Solved'] = ''
                enhanced_df['LeetCode_Hard_Solved'] = ''
                enhanced_df['LeetCode_Status'] = ''
                enhanced_df['HackerRank_Total_Badges'] = ''
                enhanced_df['HackerRank_Total_Stars'] = ''
                #enhanced_df['HackerRank_Badge_Details'] = ''
                enhanced_df['HackerRank_Status'] = ''
                #enhanced_df['Data_Fetch_Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_students = len(enhanced_df)
                
                for idx, row in enhanced_df.iterrows():
                    progress = (idx + 1) / total_students
                    progress_bar.progress(progress)
                    status_text.text(f"Processing student {idx + 1}/{total_students}: {row['Roll Number']}")
                    
                    # Fetch LeetCode data
                    leetcode_url = row['LeetCode profile']
                    if pd.notna(leetcode_url) and leetcode_url != '' and 'leetcode.com' in str(leetcode_url):
                        try:
                            username = str(leetcode_url).rstrip('/').split('/')[-1]
                            if username not in ['profile', 'account', 'login', '']:
                                stats_api_url = f"https://leetcode-stats-api.herokuapp.com/{username}"
                                stats_response = requests.get(stats_api_url, timeout=5)
                                
                                if stats_response.status_code == 200:
                                    stats = stats_response.json()
                                    enhanced_df.at[idx, 'LeetCode_Total_Solved'] = stats.get('totalSolved', 0)
                                    enhanced_df.at[idx, 'LeetCode_Easy_Solved'] = stats.get('easySolved', 0)
                                    enhanced_df.at[idx, 'LeetCode_Medium_Solved'] = stats.get('mediumSolved', 0)
                                    enhanced_df.at[idx, 'LeetCode_Hard_Solved'] = stats.get('hardSolved', 0)
                                    enhanced_df.at[idx, 'LeetCode_Status'] = 'Success'
                                else:
                                    enhanced_df.at[idx, 'LeetCode_Status'] = 'Failed'
                        except:
                            enhanced_df.at[idx, 'LeetCode_Status'] = 'Error'
                    else:
                        enhanced_df.at[idx, 'LeetCode_Status'] = 'No URL'
                    
                    # Fetch HackerRank data using new SVG parsing method
                    hackerrank_url = row['Hackerrank profile']
                    if pd.notna(hackerrank_url) and hackerrank_url != '' and 'hackerrank.com' in str(hackerrank_url):
                        try:
                            username = str(hackerrank_url).rstrip('/').split('/')[-1]
                            badges = fetch_hackerrank_badges_svg(username)
                            
                            if badges:
                                total_badges = len(badges)
                                total_stars = sum(badge['Stars'] for badge in badges if isinstance(badge['Stars'], (int, float)))
                                badge_summary = "; ".join([f"{badge['Badge Name']}({badge['Stars']}★)" for badge in badges])
                                
                                enhanced_df.at[idx, 'HackerRank_Total_Badges'] = total_badges
                                enhanced_df.at[idx, 'HackerRank_Total_Stars'] = total_stars
                                #enhanced_df.at[idx, 'HackerRank_Badge_Details'] = badge_summary
                                enhanced_df.at[idx, 'HackerRank_Status'] = 'Success'
                            else:
                                enhanced_df.at[idx, 'HackerRank_Status'] = 'No Badges Found'
                        except:
                            enhanced_df.at[idx, 'HackerRank_Status'] = 'Error'
                    else:
                        enhanced_df.at[idx, 'HackerRank_Status'] = 'No URL'
                    
                    # Add small delay to avoid overwhelming servers
                    time.sleep(0.2)  # Slightly increased delay for better reliability
                
                progress_bar.progress(1.0)
                status_text.text("Data processing completed!")
                
                # Create downloadable file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"student_data_enhanced_{timestamp}.xlsx"
                
                # Convert to Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    enhanced_df.to_excel(writer, index=False, sheet_name='Student_Data')
                
                # Create download button
                st.success("✅ Data processing completed!")
                st.download_button(
                    label="📥 Download Enhanced Student Data (Excel)",
                    data=output.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                # Also provide CSV option
                csv = enhanced_df.to_csv(index=False)
                csv_filename = f"student_data_enhanced_{timestamp}.csv"
                st.download_button(
                    label="📥 Download Enhanced Student Data (CSV)",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv"
                )
                
                # Display summary statistics
                st.markdown("### 📈 Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    leetcode_success = len(enhanced_df[enhanced_df['LeetCode_Status'] == 'Success'])
                    st.metric("LeetCode Data Fetched", f"{leetcode_success}/{total_students}")
                
                with col2:
                    hackerrank_success = len(enhanced_df[enhanced_df['HackerRank_Status'] == 'Success'])
                    st.metric("HackerRank Data Fetched", f"{hackerrank_success}/{total_students}")
                
                with col3:
                    avg_cgpa = enhanced_df['CGPA'].mean()
                    st.metric("Average CGPA", f"{avg_cgpa:.2f}")
                
                with col4:
                    students_with_backlogs = len(enhanced_df[enhanced_df['Total Backlogs'] > 0])
                    st.metric("Students with Backlogs", f"{students_with_backlogs}/{total_students}")
                
                # Additional HackerRank statistics
                if hackerrank_success > 0:
                    # Convert badge counts to numeric, handling empty strings
                    badge_counts = pd.to_numeric(enhanced_df['HackerRank_Total_Badges'], errors='coerce').fillna(0)
                    star_counts = pd.to_numeric(enhanced_df['HackerRank_Total_Stars'], errors='coerce').fillna(0)
                    
                    st.markdown("#### 🎖️ HackerRank Badge Statistics")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        avg_badges = badge_counts.mean()
                        st.metric("Average Badges per Student", f"{avg_badges:.1f}")
                    
                    with col2:
                        avg_stars = star_counts.mean()
                        st.metric("Average Stars per Student", f"{avg_stars:.1f}")
                    
                    with col3:
                        max_badges = badge_counts.max()
                        st.metric("Maximum Badges", f"{int(max_badges)}")

else:
    st.info("Please upload a CSV file to proceed.")

# Footer
st.markdown("---")
st.markdown("**Note:** This dashboard fetches real-time data from LeetCode and HackerRank. The new SVG parsing method provides more accurate badge information than the previous OCR approach.")



'''
import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json
from io import BytesIO
import base64
import time
import re
from bs4 import BeautifulSoup

def fetch_hackerrank_badges_svg(username):
    """
    Fetch HackerRank badges by parsing SVG structure directly
    Returns list of dictionaries with badge names and star counts
    """
    # Predefined list of valid HackerRank badges
    VALID_HACKERRANK_BADGES = {
        'Problem Solving', 'Java', 'Python', 'C Language', 'Cpp', 'C#', 'JavaScript',
        'Sql', '30 Days of Code', '10 Days of JavaScript', '10 Days of Statistics',
        'Algorithms', 'Data Structures', 'Regex', 'Artificial Intelligence',
        'Databases', 'Shell', 'Linux Shell', 'Functional Programming',
        'Mathematics', 'Days of ML', 'Rust', 'Kotlin', 'Swift', 'Scala',
        'Ruby', 'Go', 'Statistics', 'Interview Preparation Kit',
        'Object Oriented Programming', 'Linux Shell', 'Security'
    }

    try:
        badge_url = f'https://hackerrank-badges.vercel.app/{username}'
        response = requests.get(badge_url, timeout=15)

        if response.status_code == 200:
            svg_xml = response.text
            soup = BeautifulSoup(svg_xml, 'xml')
            
            # Debug info
            
            # Look for badge information in the SVG
            text_elements = soup.find_all('text')
            
            # Look for star sections - this is the key structure
            star_sections = soup.find_all('g', class_='star-section')
            
            # Look for individual badge stars
            badge_stars = soup.find_all('svg', class_='badge-star')
            
            # Display all text content to understand the structure
            all_texts = []
            for text in text_elements:
                text_content = text.get_text().strip()
                if text_content and len(text_content) > 1:
                    all_texts.append(text_content)
            
            
            
            # Analyze star sections
            for i, star_section in enumerate(star_sections):
                stars_in_section = star_section.find_all('svg', class_='badge-star')
            
            # Try to identify actual badges by looking for meaningful patterns
            badge_keywords = ['java', 'python', 'sql', 'javascript', 'cpp', 'problem solving', 
                            'algorithms', 'data structures', '30 days', '10 days', 'ruby', 
                            'swift', 'golang', 'rust', 'kotlin', 'scala', 'c', 'shell',
                            'functional programming', 'object oriented programming']
            
            real_badges = []
            
            # Strategy: Match badges with their corresponding star sections
            # The structure seems to be: badge text + associated star-section
            for text in all_texts:
                text_lower = text.lower()
                for keyword in badge_keywords:
                    if keyword in text_lower:
                        
                        # ✅ Check if badge is in VALID_HACKERRANK_BADGES
                        text_title = text.strip().title()
                        if text_title not in VALID_HACKERRANK_BADGES:
                            continue  # Skip if not a valid badge name
                        
                        # Find the text element in the soup
                        text_elem = None
                        for elem in text_elements:
                            if elem.get_text().strip().lower() == text_lower:
                                text_elem = elem
                                break

                        
                        stars = 0
                        if text_elem:
                            # Strategy 1: Look for star-section in the same parent or nearby elements
                            # Traverse up the DOM tree to find associated star sections
                            current = text_elem
                            found_stars = False
                            
                            # Check multiple levels up the DOM tree
                            for level in range(5):  # Check up to 5 levels up
                                if current is None:
                                    break
                                    
                                # Look for star-section in current element
                                star_section = current.find('g', class_='star-section')
                                if star_section:
                                    badge_star_elements = star_section.find_all('svg', class_='badge-star')
                                    stars = len(badge_star_elements)
                                    found_stars = True
                                    break
                                
                                # Look for star-section in siblings
                                if current.parent:
                                    sibling_star_sections = current.parent.find_all('g', class_='star-section')
                                    if sibling_star_sections:
                                        # Take the first star section found (assuming it's related)
                                        badge_star_elements = sibling_star_sections[0].find_all('svg', class_='badge-star')
                                        stars = len(badge_star_elements)
                                        found_stars = True
                                        break
                                
                                current = current.parent
                            
                            # Strategy 2: If no direct association found, try positional matching
                            if not found_stars and star_sections:
                                
                                # Get text position
                                text_x = text_elem.get('x', '0')
                                text_y = text_elem.get('y', '0')
                                
                                try:
                                    text_x_num = float(text_x) if str(text_x).replace('.', '').replace('-', '').isdigit() else 0
                                    text_y_num = float(text_y) if str(text_y).replace('.', '').replace('-', '').isdigit() else 0
                                    
                                    closest_star_section = None
                                    min_distance = float('inf')
                                    
                                    for star_section in star_sections:
                                        # Get star section position from transform attribute
                                        transform = star_section.get('transform', '')
                                        if 'translate' in transform:
                                            # Extract translate values
                                            import re
                                            translate_match = re.search(r'translate\(([^,]+),\s*([^)]+)\)', transform)
                                            if translate_match:
                                                try:
                                                    star_x = float(translate_match.group(1))
                                                    star_y = float(translate_match.group(2))
                                                    
                                                    distance = ((star_x - text_x_num) ** 2 + (star_y - text_y_num) ** 2) ** 0.5
                                                    if distance < min_distance:
                                                        min_distance = distance
                                                        closest_star_section = star_section
                                                except:
                                                    continue
                                    
                                    if closest_star_section:
                                        badge_star_elements = closest_star_section.find_all('svg', class_='badge-star')
                                        stars = len(badge_star_elements)
                                        found_stars = True
                                        
                                except:
                                    pass
                            
                            # Strategy 3: Simple distribution if we have star sections
                            if not found_stars and star_sections:
                                st.write("  📊 Using simple distribution strategy...")
                                # Count total stars and distribute among badges
                                total_star_elements = soup.find_all('svg', class_='badge-star')
                                total_badges = len([t for t in all_texts if any(kw in t.lower() for kw in badge_keywords)])
                                if total_badges > 0:
                                    stars = len(total_star_elements) // total_badges
                                    st.write(f"  ⭐ Estimated {stars} stars ({len(total_star_elements)} total / {total_badges} badges)")
                        
                        real_badges.append({
                            'Badge Name': text.title(),
                            'Stars': stars
                        })
                        
                        break  # Found this badge, don't check other keywords
            
            # Remove duplicates
            seen = set()
            unique_badges = []
            for badge in real_badges:
                badge_key = badge['Badge Name'].lower()
                if badge_key not in seen:
                    seen.add(badge_key)
                    unique_badges.append(badge)
            
            
            
            return unique_badges if unique_badges else None
            
        else:
            st.write(f"HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        st.write(f"Exception occurred: {str(e)}")
        return None

# Set page config as the very first Streamlit command
st.set_page_config(page_title="Student Performance Dashboard", layout="wide")

# Load student data
@st.cache_data
def load_student_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    return df

st.title("📊 Student Performance Dashboard")

st.header("📁 Upload Student Data")



# File uploader
uploaded_file = st.file_uploader(
    "Choose a CSV file", 
    type="csv",
    help="Upload a CSV file containing student data with required columns"
)
df = load_student_data(uploaded_file)


# Sidebar for navigation
st.sidebar.title("Navigation")
option = st.sidebar.selectbox("Choose Option", ["Individual Student", "Bulk Data Download"])

if option == "Individual Student":
    st.header("Individual Student Analysis")
    
    roll = st.text_input("Enter Roll Number (e.g., 23A31A4401):").strip().upper()

    if roll:
        student = df[df['Roll Number'].str.upper() == roll]
        if not student.empty:
            data = student.iloc[0]

            # Display basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎓 CGPA", f"{data['CGPA']}")
            with col2:
                st.metric("📚 Total Backlogs", f"{data['Total Backlogs']}")
            with col3:
                st.metric("📋 Roll Number", data['Roll Number'])

            # Create tabs for different sections
            tab1, tab2, tab3 = st.tabs(["🧠 LeetCode Stats", "🎖️ HackerRank Stats", "📊 Performance Summary"])

            with tab1:
                st.markdown("### 🧠 LeetCode Statistics")
                leetcode_url = data['Leet code links']
                
                if pd.notna(leetcode_url) and leetcode_url != '' and 'leetcode.com' in str(leetcode_url):
                    if st.button("Fetch LeetCode Stats", key="leetcode_btn"):
                        with st.spinner("Fetching LeetCode data..."):
                            try:
                                # Extract username from URL
                                username = str(leetcode_url).rstrip('/').split('/')[-1]
                                if username in ['profile', 'account', 'login', '']:
                                    # Try to extract username from URL path
                                    url_parts = str(leetcode_url).split('/')
                                    username = next((part for part in url_parts if part.startswith('u/') or part.startswith('profile/')), '').replace('u/', '').replace('profile/', '')
                                
                                if username:
                                    # LeetCode Stats API
                                    stats_api_url = f"https://leetcode-stats-api.herokuapp.com/{username}"
                                    stats_response = requests.get(stats_api_url, timeout=10)
                                    
                                    if stats_response.status_code == 200:
                                        stats = stats_response.json()
                                        
                                        # Display basic stats
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("✅ Total Solved", stats.get('totalSolved', 0))
                                        with col2:
                                            st.metric("⭐ Easy Problems", stats.get('easySolved', 0))
                                        with col3:
                                            st.metric("🟠 Medium Problems", stats.get('mediumSolved', 0))
                                        with col4:
                                            st.metric("🔴 Hard Problems", stats.get('hardSolved', 0))
                                        
                                        # Additional stats if available
                                        if 'acceptanceRate' in stats:
                                            st.metric("📈 Acceptance Rate", f"{stats['acceptanceRate']:.1f}%")
                                        if 'ranking' in stats:
                                            st.metric("🏆 Ranking", stats['ranking'])
                                    
                                    # Try to fetch submission timeline (Alternative API)
                                    st.markdown("#### 📅 Recent Activity Timeline")
                                    try:
                                        # GraphQL query for LeetCode submissions
                                        graphql_url = "https://leetcode.com/graphql"
                                        query = """
                                        query recentSubmissions($username: String!) {
                                            recentSubmissionList(username: $username) {
                                                title
                                                titleSlug
                                                timestamp
                                                statusDisplay
                                                lang
                                            }
                                        }
                                        """
                                        
                                        headers = {
                                            'Content-Type': 'application/json',
                                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                        }
                                        
                                        response = requests.post(
                                            graphql_url, 
                                            json={'query': query, 'variables': {'username': username}}, 
                                            headers=headers,
                                            timeout=10
                                        )
                                        
                                        if response.status_code == 200:
                                            submission_data = response.json()
                                            submissions = submission_data.get('data', {}).get('recentSubmissionList', [])
                                            
                                            if submissions:
                                                # Create DataFrame for submissions
                                                df_submissions = pd.DataFrame(submissions[:10])  # Show last 10 submissions
                                                df_submissions['timestamp'] = pd.to_datetime(df_submissions['timestamp'], unit='s')
                                                df_submissions['date'] = df_submissions['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
                                                
                                                st.dataframe(
                                                    df_submissions[['title', 'statusDisplay', 'lang', 'date']], 
                                                    use_container_width=True
                                                )
                                            else:
                                                st.info("No recent submissions found or profile is private.")
                                        else:
                                            st.warning("Could not fetch submission timeline. Profile might be private.")
                                    
                                    except Exception as e:
                                        st.warning(f"Timeline fetch failed: Could not retrieve submission history")
                                    
                                else:
                                    st.error("Could not extract username from LeetCode URL")
                            
                            except requests.exceptions.RequestException:
                                st.error("Failed to fetch LeetCode stats. Please check the URL or try again later.")
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                else:
                    st.warning("No valid LeetCode URL found for this student.")

            with tab2:
                st.markdown("### 🎖️ HackerRank Statistics")
                hackerrank_url = data['Hackerrank profile link']
                
                if pd.notna(hackerrank_url) and hackerrank_url != '' and 'hackerrank.com' in str(hackerrank_url):
                    if st.button("Fetch HackerRank Stats", key="hackerrank_btn"):
                        with st.spinner("Fetching HackerRank data..."):
                            try:
                                # Extract username from URL
                                username = str(hackerrank_url).rstrip('/').split('/')[-1]
                                
                                # Display the badge image first
                                badge_image_url = f"https://hackerrank-badges.vercel.app/{username}"
                                st.image(badge_image_url, caption=f"HackerRank Badges for {username}", use_column_width=True)
                                
                                # Use the new SVG parsing function
                                st.markdown("#### 🏆 Badge Details")
                                
                                # Add a debug checkbox
                                
                                
                                
                                badges = fetch_hackerrank_badges_svg(username)
                                
                                if badges:
                                    st.success(f"✅ Successfully extracted {len(badges)} badges!")
                                    
                                    # Create DataFrame for better display
                                    badges_df = pd.DataFrame(badges)
                                    
                                    # Display badges in a nice format
                                    st.dataframe(badges_df, use_container_width=True)
                                    
                                    # Show summary statistics
                                    total_badges = len(badges)
                                    total_stars = sum(badge['Stars'] for badge in badges if isinstance(badge['Stars'], int))
                                    avg_stars = total_stars / total_badges if total_badges > 0 else 0
                                    
                                    # Display summary metrics
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("🎖️ Total Badges", total_badges)
                                    with col2:
                                        st.metric("⭐ Total Stars", total_stars)
                                    
                                    
                                    # Show badges grouped by star count
                                    st.markdown("#### ⭐ Badges by Star Rating")
                                    star_groups = {}
                                    for badge in badges:
                                        stars = badge['Stars']
                                        if isinstance(stars, int):
                                            if stars not in star_groups:
                                                star_groups[stars] = []
                                            star_groups[stars].append(badge['Badge Name'])
                                    
                                    for stars in sorted(star_groups.keys(), reverse=True):
                                        badge_names = ", ".join(star_groups[stars])
                                        star_emoji = "⭐" * stars if stars > 0 else "⚪"
                                        st.write(f"{star_emoji} **{stars} Star{'s' if stars != 1 else ''}:** {badge_names}")
                                    
                                    # Export badges data
                                    st.markdown("#### 📥 Export Badge Data")
                                    badges_json = json.dumps(badges, indent=2)
                                    st.download_button(
                                        label="Download Badge Data as JSON",
                                        data=badges_json,
                                        file_name=f"hackerrank_badges_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                        mime="application/json"
                                    )
                                    
                                else:
                                    st.warning("⚠️ Could not extract badge information from the SVG.")
                                    
                                    # Provide manual entry option
                                    st.markdown("### ✏️ Manual Badge Entry")
                                    st.info("Since automatic extraction failed, you can manually enter badge information by looking at the image above.")
                                    
                                    with st.form(f"manual_badges_{username}"):
                                        st.markdown("**Enter badge information manually:**")
                                        
                                        num_badges = st.number_input("How many badges do you see?", min_value=0, max_value=20, value=0)
                                        
                                        manual_badges = []
                                        if num_badges > 0:
                                            for i in range(num_badges):
                                                col1, col2 = st.columns(2)
                                                with col1:
                                                    badge_name = st.text_input(f"Badge {i+1} Name:", key=f"name_{i}")
                                                with col2:
                                                    badge_stars = st.number_input(f"Badge {i+1} Stars:", min_value=0, max_value=5, value=0, key=f"stars_{i}")
                                                
                                                if badge_name:
                                                    manual_badges.append({"Badge Name": badge_name, "Stars": badge_stars})
                                        
                                        submitted = st.form_submit_button("💾 Save Manual Badges")
                                        
                                        if submitted and manual_badges:
                                            st.success(f"✅ Manually entered {len(manual_badges)} badges!")
                                            manual_df = pd.DataFrame(manual_badges)
                                            st.dataframe(manual_df, use_container_width=True)
                                            
                                            # Show summary for manual badges
                                            total_manual_stars = sum(badge['Stars'] for badge in manual_badges)
                                            st.metric("Total Manual Stars", total_manual_stars)
                                    
                                    # Show troubleshooting tips
                                    with st.expander("🔧 Troubleshooting Tips"):
                                        st.markdown("""
                                        **Common issues and solutions:**
                                        
                                        1. **Profile is Private**: Make sure the HackerRank profile is public
                                        2. **Username Issue**: Check if the username extracted from URL is correct
                                        3. **No Badges**: User might not have earned any badges yet
                                        4. **Server Issue**: The badge service might be temporarily down
                                        5. **SVG Structure Changed**: The badge generator might have updated its format
                                        
                                        **What you can do:**
                                        - Enable debug mode above to see the raw SVG structure
                                        - Try accessing the URL directly: `https://hackerrank-badges.vercel.app/{username}`
                                        - Use manual entry if automatic parsing fails
                                        """)
                                
                            except requests.exceptions.RequestException:
                                st.error("Failed to fetch HackerRank data. Please check the URL or try again later.")
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                                
                                # Show error details in debug mode
                                if st.checkbox("Show error details", key=f"error_debug_{username}"):
                                    st.code(str(e))
                else:
                    st.warning("No valid HackerRank URL found for this student.")

            with tab3:
                st.markdown("### 📊 Performance Summary")
                
                # Performance metrics
                cgpa_status = "Excellent" if data['CGPA'] >= 9.0 else "Good" if data['CGPA'] >= 8.0 else "Average" if data['CGPA'] >= 7.0 else "Below Average"
                backlog_status = "No Backlogs" if data['Total Backlogs'] == 0 else f"{data['Total Backlogs']} Backlog(s)"
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**CGPA Status:** {cgpa_status}")
                    st.info(f"**Backlog Status:** {backlog_status}")
                with col2:
                    st.info(f"**HackerRank Profile:** {'✅ Available' if pd.notna(data['Hackerrank profile link']) else '❌ Not Available'}")
                    st.info(f"**LeetCode Profile:** {'✅ Available' if pd.notna(data['Leet code links']) else '❌ Not Available'}")

        else:
            st.error("❌ Roll number not found.")

elif option == "Bulk Data Download":
    st.header("Bulk Data Download")
    
    st.markdown("Download comprehensive data for all students including LeetCode and HackerRank statistics.")
    
    if st.button("📥 Generate and Download Student Data", key="bulk_download"):
        with st.spinner("Fetching data for all students... This may take a while..."):
            
            # Create a copy of the original dataframe
            enhanced_df = df.copy()
            
            # Add new columns for enhanced data
            enhanced_df['LeetCode_Total_Solved'] = ''
            enhanced_df['LeetCode_Easy_Solved'] = ''
            enhanced_df['LeetCode_Medium_Solved'] = ''
            enhanced_df['LeetCode_Hard_Solved'] = ''
            enhanced_df['LeetCode_Status'] = ''
            enhanced_df['HackerRank_Total_Badges'] = ''
            enhanced_df['HackerRank_Total_Stars'] = ''
            enhanced_df['HackerRank_Badge_Details'] = ''
            enhanced_df['HackerRank_Status'] = ''
            enhanced_df['Data_Fetch_Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_students = len(enhanced_df)
            
            for idx, row in enhanced_df.iterrows():
                progress = (idx + 1) / total_students
                progress_bar.progress(progress)
                status_text.text(f"Processing student {idx + 1}/{total_students}: {row['Roll Number']}")
                
                # Fetch LeetCode data
                leetcode_url = row['Leet code links']
                if pd.notna(leetcode_url) and leetcode_url != '' and 'leetcode.com' in str(leetcode_url):
                    try:
                        username = str(leetcode_url).rstrip('/').split('/')[-1]
                        if username not in ['profile', 'account', 'login', '']:
                            stats_api_url = f"https://leetcode-stats-api.herokuapp.com/{username}"
                            stats_response = requests.get(stats_api_url, timeout=5)
                            
                            if stats_response.status_code == 200:
                                stats = stats_response.json()
                                enhanced_df.at[idx, 'LeetCode_Total_Solved'] = stats.get('totalSolved', 0)
                                enhanced_df.at[idx, 'LeetCode_Easy_Solved'] = stats.get('easySolved', 0)
                                enhanced_df.at[idx, 'LeetCode_Medium_Solved'] = stats.get('mediumSolved', 0)
                                enhanced_df.at[idx, 'LeetCode_Hard_Solved'] = stats.get('hardSolved', 0)
                                enhanced_df.at[idx, 'LeetCode_Status'] = 'Success'
                            else:
                                enhanced_df.at[idx, 'LeetCode_Status'] = 'Failed'
                    except:
                        enhanced_df.at[idx, 'LeetCode_Status'] = 'Error'
                else:
                    enhanced_df.at[idx, 'LeetCode_Status'] = 'No URL'
                
                # Fetch HackerRank data using new SVG parsing method
                hackerrank_url = row['Hackerrank profile link']
                if pd.notna(hackerrank_url) and hackerrank_url != '' and 'hackerrank.com' in str(hackerrank_url):
                    try:
                        username = str(hackerrank_url).rstrip('/').split('/')[-1]
                        badges = fetch_hackerrank_badges_svg(username)
                        
                        if badges:
                            total_badges = len(badges)
                            total_stars = sum(badge['Stars'] for badge in badges)
                            badge_summary = "; ".join([f"{badge['Badge Name']}({badge['Stars']}★)" for badge in badges])
                            
                            enhanced_df.at[idx, 'HackerRank_Total_Badges'] = total_badges
                            enhanced_df.at[idx, 'HackerRank_Total_Stars'] = total_stars
                            enhanced_df.at[idx, 'HackerRank_Badge_Details'] = badge_summary
                            enhanced_df.at[idx, 'HackerRank_Status'] = 'Success'
                        else:
                            enhanced_df.at[idx, 'HackerRank_Status'] = 'No Badges Found'
                    except:
                        enhanced_df.at[idx, 'HackerRank_Status'] = 'Error'
                else:
                    enhanced_df.at[idx, 'HackerRank_Status'] = 'No URL'
                
                # Add small delay to avoid overwhelming servers
                time.sleep(0.2)  # Slightly increased delay for better reliability
            
            progress_bar.progress(1.0)
            status_text.text("Data processing completed!")
            
            # Create downloadable file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"student_data_enhanced_{timestamp}.xlsx"
            
            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                enhanced_df.to_excel(writer, index=False, sheet_name='Student_Data')
            
            # Create download button
            st.success("✅ Data processing completed!")
            st.download_button(
                label="📥 Download Enhanced Student Data (Excel)",
                data=output.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Also provide CSV option
            csv = enhanced_df.to_csv(index=False)
            csv_filename = f"student_data_enhanced_{timestamp}.csv"
            st.download_button(
                label="📥 Download Enhanced Student Data (CSV)",
                data=csv,
                file_name=csv_filename,
                mime="text/csv"
            )
            
            # Display summary statistics
            st.markdown("### 📈 Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                leetcode_success = len(enhanced_df[enhanced_df['LeetCode_Status'] == 'Success'])
                st.metric("LeetCode Data Fetched", f"{leetcode_success}/{total_students}")
            
            with col2:
                hackerrank_success = len(enhanced_df[enhanced_df['HackerRank_Status'] == 'Success'])
                st.metric("HackerRank Data Fetched", f"{hackerrank_success}/{total_students}")
            
            with col3:
                avg_cgpa = enhanced_df['CGPA'].mean()
                st.metric("Average CGPA", f"{avg_cgpa:.2f}")
            
            with col4:
                students_with_backlogs = len(enhanced_df[enhanced_df['Total Backlogs'] > 0])
                st.metric("Students with Backlogs", f"{students_with_backlogs}/{total_students}")
            
            # Additional HackerRank statistics
            if hackerrank_success > 0:
                # Convert badge counts to numeric, handling empty strings
                badge_counts = pd.to_numeric(enhanced_df['HackerRank_Total_Badges'], errors='coerce').fillna(0)
                star_counts = pd.to_numeric(enhanced_df['HackerRank_Total_Stars'], errors='coerce').fillna(0)
                
                st.markdown("#### 🎖️ HackerRank Badge Statistics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    avg_badges = badge_counts.mean()
                    st.metric("Average Badges per Student", f"{avg_badges:.1f}")
                
                with col2:
                    avg_stars = star_counts.mean()
                    st.metric("Average Stars per Student", f"{avg_stars:.1f}")
                
                with col3:
                    max_badges = badge_counts.max()
                    st.metric("Maximum Badges", f"{int(max_badges)}")

# Footer
st.markdown("---")
st.markdown("**Note:** This dashboard fetches real-time data from LeetCode and HackerRank. The new SVG parsing method provides more accurate badge information than the previous OCR approach.")
'''


