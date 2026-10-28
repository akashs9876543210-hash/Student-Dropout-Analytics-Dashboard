import streamlit as st
import pandas as pd
import plotly.express as px

# Set up the web page
st.set_page_config(page_title="Student Dropout Analytics", page_icon="🎓", layout="wide")

# Load data once and save it in memory to keep the app fast
@st.cache_data
def load_student_data(file_path):
    df = pd.read_csv(file_path)
    # Change numbers to readable words for our charts
    df['Status'] = df['dropout'].map({0: 'Retained/Graduated', 1: 'Dropped Out'})
    df['Student Type'] = df['international_student'].map({0: 'National (Domestic)', 1: 'International'})
    
    # ENGINEER NEW DATA: Create Rural vs Urban based on Commute Time
    # < 30 mins = Urban, 30-60 mins = Suburban, > 60 mins = Rural
    df['Location_Type'] = pd.cut(df['commute_time_mins'], 
                                 bins=[-1, 30, 60, 999], 
                                 labels=['Urban (Local)', 'Suburban', 'Rural (Distant)'])
    return df

# Relative path so it works perfectly on Streamlit Cloud
FILE_PATH = "student_dropout_risk_2026.csv"

try:
    # 1. GET THE DATA
    df = load_student_data(FILE_PATH)
    
    # 2. BUILD THE SIDE MENU
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135810.png", width=100) 
    st.sidebar.header("🔍 Filter Data")
    
    selected_gender = st.sidebar.multiselect("Select Gender", options=df['gender'].unique(), default=df['gender'].unique())
    selected_course = st.sidebar.multiselect("Course Type", options=df['course_type'].unique(), default=df['course_type'].unique())
    selected_income = st.sidebar.multiselect("Family Income", options=df['family_income_level'].unique(), default=df['family_income_level'].unique())

    # Update the data based on filters
    filtered_df = df[
        (df['gender'].isin(selected_gender)) & 
        (df['course_type'].isin(selected_course)) &
        (df['family_income_level'].isin(selected_income))
    ]

    # 3. MAIN TITLES AND QUICK STATS
    st.title("🎓 Interactive Student Dropout Analytics")
    st.markdown("Use the side menu to filter the data. Discover the probability and reasons behind student dropouts.")
    
    total_students = len(filtered_df)
    total_dropouts = filtered_df['dropout'].sum()
    dropout_rate = (total_dropouts / total_students * 100) if total_students > 0 else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="👥 Total Students", value=f"{total_students:,}")
    kpi2.metric(label="⚠️ Total Dropouts", value=f"{total_dropouts:,}")
    kpi3.metric(label="📉 Dropout Rate", value=f"{dropout_rate:.1f}%")
    
    st.divider()

    # 4. PROBABILITY & REASONS
    st.subheader("🧠 Top Reasons for Dropping Out")
    st.markdown("This chart mathematically calculates what habits increase or decrease the risk of dropping out.")
    
    habits = ['gpa_semester_1', 'attendance_rate', 'stress_level', 'commute_time_mins', 
              'sleep_hours', 'missed_deadlines', 'tuition_up_to_date']
    
    correlations = filtered_df[habits + ['dropout']].corr()['dropout'].drop('dropout').sort_values()
    corr_df = pd.DataFrame({'Factor': correlations.index, 'Impact': correlations.values})
    corr_df['Effect'] = corr_df['Impact'].apply(lambda x: 'Increases Risk' if x > 0 else 'Reduces Risk')
    corr_df['Factor'] = corr_df['Factor'].str.replace('_', ' ').str.title() 
    
    fig_reasons = px.bar(corr_df, x='Impact', y='Factor', color='Effect', orientation='h',
                         color_discrete_map={'Increases Risk': '#EF553B', 'Reduces Risk': '#00CC96'},
                         title="What drives students to drop out?")
    st.plotly_chart(fig_reasons, use_container_width=True)

    st.divider()

    # 5. GLOBAL, REGIONAL & RURAL/URBAN ANALYSIS
    st.subheader("🌍 Regional Analysis: Where do our students come from?")
    
    col_int1, col_int2, col_int3 = st.columns(3)
    
    with col_int1:
        # Chart: National vs International Dropout Rate
        type_dropout = filtered_df.groupby('Student Type')['dropout'].mean().reset_index()
        type_dropout['Dropout Rate (%)'] = type_dropout['dropout'] * 100
        fig_type = px.bar(type_dropout, x='Student Type', y='Dropout Rate (%)', 
                          color='Student Type', text_auto='.1f',
                          color_discrete_sequence=['#636EFA', '#FFA15A'],
                          title="National vs. International")
        st.plotly_chart(fig_type, use_container_width=True)

    with col_int2:
        # Chart: RURAL VS URBAN DROPOUT RISK
        loc_dropout = filtered_df.groupby('Location_Type')['dropout'].mean().reset_index()
        loc_dropout['Dropout Rate (%)'] = loc_dropout['dropout'] * 100
        fig_loc = px.bar(loc_dropout, x='Location_Type', y='Dropout Rate (%)', 
                         color='Location_Type', text_auto='.1f',
                         color_discrete_sequence=px.colors.qualitative.Safe,
                         title="Rural vs. Urban Dropout Risk")
        st.plotly_chart(fig_loc, use_container_width=True)
        
    with col_int3:
        # Chart: Top Nationalities by Volume
        nat_counts = filtered_df['nationality'].value_counts().reset_index().head(10)
        nat_counts.columns = ['Nationality', 'Student Count']
        fig_nat = px.bar(nat_counts, x='Nationality', y='Student Count', 
                         title="Top 10 Nationalities", 
                         color='Student Count', color_continuous_scale='Blues')
        st.plotly_chart(fig_nat, use_container_width=True)

    st.divider()

    # 6. STUNNING VISUAL GRAPHS
    st.subheader("📊 Deep Dive Visualizations")
    
    col1, col2 = st.columns(2)

    with col1:
        fig_sunburst = px.sunburst(filtered_df, path=['course_type', 'family_income_level', 'Status'], 
                                   color='Status', color_discrete_map={'Retained/Graduated':'#00CC96', 'Dropped Out':'#EF553B'},
                                   title="Click rings to zoom: Course ➔ Income ➔ Status")
        st.plotly_chart(fig_sunburst, use_container_width=True)

    with col2:
        income_dropout = filtered_df.groupby('family_income_level')['dropout'].mean().reset_index()
        income_dropout['Dropout Rate (%)'] = income_dropout['dropout'] * 100
        fig_bar = px.bar(income_dropout, x='family_income_level', y='Dropout Rate (%)',
                         color='family_income_level', text_auto='.1f',
                         color_discrete_sequence=px.colors.qualitative.Pastel,
                         title="Dropout Rate by Family Income Level")
        st.plotly_chart(fig_bar, use_container_width=True)

    fig_heat = px.density_heatmap(filtered_df, x='attendance_rate', y='gpa_semester_1', facet_col='Status',
                                  color_continuous_scale='Viridis',
                                  title="Heatmap: Attendance vs GPA (Compare Dropouts with Graduates)")
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    # 7. AGE GROUP DISTRIBUTION
    st.subheader("🎂 Age Group Distribution")
    fig_age = px.histogram(filtered_df, x='age', color='Status', barmode='group', nbins=15,
                           color_discrete_map={'Retained/Graduated':'#00CC96', 'Dropped Out':'#EF553B'},
                           title="Student Age vs. Dropout Risk")
    fig_age.update_layout(xaxis_title="Student Age", yaxis_title="Number of Students")
    st.plotly_chart(fig_age, use_container_width=True)

    st.divider()

    # 8. HOW TO RESOLVE THIS (ACTION PLAN FOR STAKEHOLDERS)
    st.subheader("💡 Strategic Action Plan: How We Can Resolve This")
    st.info("""
    **Based on the data shown above, here are actionable steps we must take to reduce the dropout rate:**
    
    1. **Rural Commuter Support (New Insight):** Based on our regional analysis, students with long commutes (Rural/Distant) face unique dropout pressures. We must offer subsidized transport passes or schedule core classes in clustered blocks to reduce their travel days.
    2. **Targeted International Support:** International students face unique pressures (visa stress, culture shock). We must launch an "Early Integration Program" during their first semester.
    3. **The "Danger Zone" Alerts:** The Attendance vs. GPA heatmap proves exactly when a student is giving up. We need to implement an automated alert system that texts an advisor the moment a student misses 3 classes in a row. 
    4. **Financial Safety Nets:** Family income heavily dictates dropout risk. We need to offer flexible tuition payment plans so students don't have to choose between working and studying.
    """)

    st.divider()

    # 9. RAW DATA TABLE
    st.subheader("📄 Filtered Student Records")
    st.dataframe(filtered_df.head(100), width="stretch")

except Exception as e:
    st.error(f"Could not load the file. Please check your file path. Error: {e}")
