import streamlit as st
import pandas as pd

# Initialize session state for storing data
if 'data' not in st.session_state:
    st.session_state.data = None

# Function to load data with validation
def load_data(performance_data_file):
    try:
        data = pd.read_csv(performance_data_file)
        if not validate_data(data):
            st.error("Data validation failed.")
            return None
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# Function to validate data
def validate_data(data):
    # Validate that required columns exist and have no null values
    required_columns = ['date', 'income', 'expense']
    for column in required_columns:
        if column not in data.columns or data[column].isnull().any():
            return False
    return True

# Main app logic
st.title('Agenda de Ganhos')

# File uploader
uploaded_file = st.file_uploader('Upload CSV', type='csv')
if uploaded_file is not None:
    st.session_state.data = load_data(uploaded_file)

if st.session_state.data is not None:
    st.subheader('Data Loaded')
    st.dataframe(st.session_state.data)
else:
    st.warning("Please upload a valid CSV file to see the data.")
