import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Page Config
st.set_page_config(page_title="ChurnBuster 360", layout="wide")

st.title("📉 ChurnBuster 360: Retention Command Center")

# Load Data
# We look for the data in the local 'data' folder which is mounted to Docker
DATA_PATH = "data/processed/final_predictions.csv"
LOG_PATH = "data/processed/email_campaign_log.csv"
# --- NEW PATH ---
IMPORTANCE_PATH = "data/model/feature_importances.csv"

# Function to load data without crashing if file missing
def load_data(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

df = load_data(DATA_PATH)
log_df = load_data(LOG_PATH)
# --- NEW LOAD ---
importance_df = load_data(IMPORTANCE_PATH)

if df is None:
    st.error("Data not found! Please run the Airflow pipeline first.")
    st.stop()

# --- FILTER CONTROLS (Sidebar) ---
st.sidebar.header("Filter Customers")

# 1. Filter by Age
min_age = int(df['age'].min())
max_age = int(df['age'].max())

age_range = st.sidebar.slider(
    'Age Range',
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)
)

# 2. Filter by City
# Get top 10 cities for cleaner display
top_cities = df['city'].value_counts().nlargest(10).index.tolist()
city_options = ['All'] + top_cities

selected_city = st.sidebar.selectbox(
    'City',
    city_options
)

# 3. Apply Filters to DataFrame
filtered_df = df[
    (df['age'] >= age_range[0]) & (df['age'] <= age_range[1])
]

if selected_city != 'All':
    filtered_df = filtered_df[filtered_df['city'] == selected_city]

# Calculate filtered high risk count for metric update
filtered_high_risk_count = len(filtered_df[filtered_df['churn_probability'] > 0.8])

st.sidebar.markdown("---")
st.sidebar.metric("Filtered High Risk Count", filtered_high_risk_count)

# --- END FILTER CONTROLS ---

# --- TOP METRICS ---
col1, col2, col3 = st.columns(3)

total_customers = len(filtered_df)
# Calculate high risk (Probability > 80%)
high_risk_count = len(filtered_df[filtered_df['churn_probability'] > 0.8])
avg_risk = filtered_df['churn_probability'].mean() * 100 if not filtered_df.empty else 0.0

col1.metric("Total Customers", total_customers)
col2.metric("High Risk Customers (>80%)", high_risk_count, delta_color="inverse")
col3.metric("Avg Churn Probability", f"{avg_risk:.1f}%")

st.markdown("---")

# --- RISK SEGMENTATION & CHARTS ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🔍 High Risk Customers (Alert List)")
    st.caption("These customers have >80% probability of churning.")
    
    high_risk_df = filtered_df[filtered_df['churn_probability'] > 0.8].sort_values('churn_probability', ascending=False)
    
    # Show a clean table
    st.dataframe(
        high_risk_df[['customer_id', 'name', 'days_since_last_txn', 'churn_probability', 'avg_txn_amount']],
        use_container_width=True
    )

with col_right:
    st.subheader("💡 Model Insights")
    
    # Create two tabs for better organization
    tab1, tab2 = st.tabs(["Feature Importance", "Prob. Distribution"])
    
    with tab1:
        if importance_df is not None:
            st.caption("How much each feature contributes to the prediction.")
            fig, ax = plt.subplots(figsize=(6, 4))
            
            # Create the Feature Importance Bar Chart
            sns.barplot(
                x='importance', 
                y='feature', 
                data=importance_df, 
                ax=ax, 
                palette="viridis"
            )
            ax.set_title('Feature Importance')
            ax.set_xlabel('Relative Importance Score')
            ax.set_ylabel('Feature')
            st.pyplot(fig)
        else:
            st.info("Feature importance data not found. Rerun the pipeline.")

    with tab2:
        st.caption("Distribution of predicted churn probabilities.")
        fig, ax = plt.subplots(figsize=(6, 4))
        # This is your original histogram
        sns.histplot(filtered_df['churn_probability'], bins=20, kde=True, ax=ax, color='red')
        ax.set_xlabel("Churn Probability (0-1)")
        ax.set_ylabel("Count of Customers")
        st.pyplot(fig)

# --- CAMPAIGN LOGS ---
st.markdown("---")
st.subheader("📧 Retention Campaign Logs (Real-time)")

if log_df is not None:
    # Display the most recent emails first
    st.dataframe(log_df, use_container_width=True, height=300) 
    st.caption(f"Total Emails Sent So Far: {len(log_df)}")
else:
    st.info("No campaign logs found yet. The 'Send Emails' task hasn't run or found targets yet.")