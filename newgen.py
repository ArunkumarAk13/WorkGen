import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from autoviz.AutoViz_Class import AutoViz_Class

st.set_page_config(page_title="WorkGEN", layout="centered")

if "page" not in st.session_state:
    st.session_state.page = "landing"
if "df" not in st.session_state:
    st.session_state.df = None
if "generated_charts" not in st.session_state:
    st.session_state.generated_charts = set()
if "autoviz_run" not in st.session_state:
    st.session_state.autoviz_run = False
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "report_content" not in st.session_state:
    st.session_state.report_content = []
if "dashboard_charts" not in st.session_state:
    st.session_state.dashboard_charts = []

def rename_duplicate_columns(df):
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '_' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    return df

def is_project_exists(project_name):
    return project_name in st.session_state.projects

def add_project(project_name, num_members, df):
    if df is None:
        st.error("No data loaded. Please upload a file to continue.")
        return False

    if 'EmpID' not in df.columns or 'JobSatisfaction' not in df.columns:
        st.error("Please ensure that the dataset contains 'EmpID' and 'JobSatisfaction' columns.")
        return False

    if is_project_exists(project_name):
        st.error(f"Project '{project_name}' already exists.")
        return False

    job_satisfaction_col = 'JobSatisfaction'
    eligible_employees = df[df[job_satisfaction_col] >= 3]

    if len(eligible_employees) < num_members:
        st.error("Not enough eligible employees to fulfill the project requirement.")
        return False

    selected_employees = eligible_employees.sample(num_members).EmpID.tolist()
    st.session_state.projects[project_name] = selected_employees
    st.success(f"Project '{project_name}' created with members: {', '.join(map(str, selected_employees))}")
    return True

def display_projects():
    if st.session_state.projects:
        st.write("### Created Projects")
        project_df = pd.DataFrame(
            [(name, ", ".join(map(str, members))) for name, members in st.session_state.projects.items()],
            columns=["Project Name", "Members (EmpID)"]
        )
        st.dataframe(project_df)

def landing_page():
    st.title("WorkGEN")
    st.subheader("A Real-Time Data Insight Platform")
    st.write("**Workforce Analytics and People Management** helps you gain insights into your workforce data with interactive visualizations and automated analysis.")
    st.image("https://i.pinimg.com/originals/00/08/10/00081094ea8cf521ccebe03095ac0365.gif", caption="Analyze Your Workforce Effectively", use_column_width=True)
    st.markdown("### Key Features:\n- Upload CSV or Excel files with your workforce data.\n- Perform automated Exploratory Data Analysis (EDA).\n- Interactive visualizations like Bar Charts, Donut Charts, Bubble Charts, and Pie Charts.")

def upload_and_preview():
    st.write("## Upload your CSV/Excel file")
    uploaded_file = st.file_uploader("Upload your file", type=['csv', 'xlsx'])

    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')): 
            df = pd.read_excel(uploaded_file)

        df = rename_duplicate_columns(df)
        st.session_state.df = df

    if st.session_state.df is not None:
        st.write("### Dataset Preview")
        st.write(st.session_state.df.head())
        st.write("### Dataset Information")
        st.write(st.session_state.df.describe())

def generate_insight_for_bar_chart(df, x_axis, y_axis):
    highest_value = df[y_axis].max()
    highest_category = df[df[y_axis] == highest_value][x_axis].values[0]

    insight_text = (
        f"It appears that high values in {y_axis} are associated with {x_axis} variations. "
        f"Some notable patterns are that the highest value in {y_axis} corresponds to {highest_category} in {x_axis}. "
        "This might indicate a trend worth further analysis."
    )
    st.session_state.report_content.append(insight_text)
    return insight_text

def generate_insight_for_pie_chart(df, categorical_col):
    highest_frequency_category = df[categorical_col].value_counts().idxmax()
    highest_frequency = df[categorical_col].value_counts().max()

    insight_text = (
        f"It appears that the highest frequency in {categorical_col} is for '{highest_frequency_category}', "
        f"with {highest_frequency} occurrences. This may highlight a dominant category that could warrant further focus."
    )
    st.session_state.report_content.append(insight_text)
    return insight_text

def visualization_and_text_gen():
    if st.session_state.df is None:
        st.error("Please upload a dataset first.")
        return
    
    st.write("### Data Visualizations")
    chart_type = st.selectbox("Select a chart type", ("Bar Chart", "Pie Chart", "Donut Chart"))
    df = st.session_state.df
    
    if chart_type == "Bar Chart":
        x_axis = st.selectbox("Select X-axis", df.columns)
        y_axis = st.selectbox("Select Y-axis", df.columns)
        chart_id = (chart_type, x_axis, y_axis)

        if x_axis and y_axis and chart_id not in st.session_state.generated_charts:
            fig = px.bar(df, x=x_axis, y=y_axis, color=x_axis, color_continuous_scale=px.colors.sequential.Plasma)
            st.plotly_chart(fig)
            st.session_state.generated_charts.add(chart_id)
            st.session_state.dashboard_charts.append(fig)

            insight_text = generate_insight_for_bar_chart(df, x_axis, y_axis)
            st.write("**Generated Insight**")
            st.write(insight_text)
            
    elif chart_type == "Pie Chart" or chart_type == "Donut Chart":
        categorical_col = st.selectbox("Select Categorical Column", df.select_dtypes(include=['object']).columns)
        chart_id = (chart_type, categorical_col)
        
        if categorical_col and chart_id not in st.session_state.generated_charts:
            fig = px.pie(df, names=categorical_col, hole=0.4 if chart_type == "Donut Chart" else 0)
            st.plotly_chart(fig)
            st.session_state.generated_charts.add(chart_id)
            st.session_state.dashboard_charts.append(fig)

            insight_text = generate_insight_for_pie_chart(df, categorical_col)
            st.write("**Generated Insight**")
            st.write(insight_text)
        
    if st.session_state.report_content:
        st.write("### Generated Text Report")
        for report in st.session_state.report_content:
            st.write(report)

        st.download_button(
            label="Download Report as Text File",
            data="\n\n".join(st.session_state.report_content),
            file_name="analysis_report.txt",
            mime="text/plain"
        )

        st.download_button(
            label="Download Report as Word File",
            data="\n\n".join(st.session_state.report_content),
            file_name="analysis_report.doc",
            mime="text/plain"
        )

def dashboard_page():
    st.write("### Dashboard - Visualized Charts with Insights")
    if not st.session_state.dashboard_charts:
        st.write("No charts have been added to the dashboard yet. Go to the Visualizations page to create charts.")
    else:
        for i, chart in enumerate(st.session_state.dashboard_charts):
            # Display each chart
            st.plotly_chart(chart)
            
            # Display the corresponding insight text below each chart
            if i < len(st.session_state.report_content):
                st.write("**Insight for this chart:**")
                st.write(st.session_state.report_content[i])

def create_project_page():
    st.write("## Create Project")

    # Check if the dataset is loaded
    if st.session_state.df is None:
        st.error("Please upload a dataset first to create a project.")
        return

    project_name = st.text_input("Enter Project Name")
    num_members = st.number_input("Enter number of members", min_value=1)
    if st.button("Create Project"):
        if add_project(project_name, num_members, st.session_state.df):
            display_projects()

def view_projects_page():
    st.write("## View Projects")

    # Check if the dataset is loaded
    if st.session_state.df is None:
        st.error("Please upload a dataset first to view projects.")
        return

    # Check if any project has been created
    if not st.session_state.projects:
        st.warning("No projects found. Please go to the create project to create a project first.")
    else:
        display_projects()

def autoviz_page(df):
    if df is None:
        st.error("Please upload a dataset first.")
        return

    if st.checkbox("Run AutoViz for Automated EDA"):
        st.write("Auto-generated Visualizations")
        AV = AutoViz_Class()
        df_av = AV.AutoViz(
            filename="",
            sep=",",
            depVar="",
            dfte=df,
            header=0,
            verbose=0,
            lowess=False,
            chart_format="png",
            max_rows_analyzed=150000,
            max_cols_analyzed=30,
        )
        for fig in plt.get_fignums():
            st.pyplot(plt.figure(fig))
        
        st.session_state.autoviz_run = True

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Go to", ["Landing", "Upload & Preview", "Create Project", "View Projects", "Visualizations", "Dashboard", "AutoViz"])

    if page == "Landing":
        landing_page()
    elif page == "Upload & Preview":
        upload_and_preview()
    elif page == "Create Project":
        create_project_page()
    elif page == "View Projects":
        view_projects_page()
    elif page == "Visualizations":
        visualization_and_text_gen()
    elif page == "Dashboard":
        dashboard_page()
    elif page == "AutoViz":
        autoviz_page(st.session_state.df)

if __name__ == "__main__":
    main()
