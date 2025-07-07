import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Set page config
st.set_page_config(
    page_title="Personal Expense Analyzer",
    page_icon="��",
    layout="wide",
    initial_sidebar_state="expanded"  # This ensures sidebar starts expanded
)

# Add sidebar title for better visibility
st.sidebar.title("Navigation")
st.sidebar.markdown("👆 Use the menu above to navigate between pages")

# Title and description
st.title("💰 Personal Expense Analyzer")
st.markdown("""
Analyze your personal finances with detailed visualizations. 
Upload your expense CSV file or use the sample data to get started.
""")

def extract_hashtags(note):
    if pd.isna(note):
        return []
    # Extract complete hashtag phrases (everything after # until the next comma/newline)
    tags = []
    notes = str(note).split("\n")
    for note in notes:
        if note.startswith('#'):
            note = note.replace('#', '')
            # Capitalize each word in the hashtag
            tag = ' '.join(word.capitalize() for word in note.split())
            tags.append(tag)
    return tags

def load_data(file):
    df = pd.read_csv(file)
    df['date'] = pd.to_datetime(df['date'])
    
    # Convert amount to float and handle income/expense
    df['amount'] = df['amount'].astype(float)
    df['transaction_type'] = df['income'].map({True: 'Income', False: 'Expense'})
    
    # Create expense amount (negative for plotting)
    df['expense_amount'] = df.apply(lambda x: -x['amount'] if x['transaction_type'] == 'Expense' else x['amount'], axis=1)
    
    # Extract hashtags from notes
    df['hashtags'] = df['note'].apply(extract_hashtags)
    
    return df

def create_summary_metrics(df):
    # Calculate metrics
    total_expenses = -df[df['transaction_type'] == 'Expense']['amount'].sum()
    total_income = df[df['transaction_type'] == 'Income']['amount'].sum()
    net_savings = total_income - total_expenses
    savings_rate = (net_savings / total_income * 100) if total_income != 0 else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col3:
        st.metric("Net Savings", f"${net_savings:,.2f}")
    with col4:
        st.metric("Savings Rate", f"{savings_rate:.1f}%")

def create_visualizations(df):
    # Time period selector
    time_periods = ['Monthly', 'Weekly', 'Daily']
    selected_period = st.selectbox('Select Time Period', time_periods)
    
    if selected_period == 'Monthly':
        date_format = '%Y-%m'
    elif selected_period == 'Weekly':
        date_format = '%Y-%W'
    else:
        date_format = '%Y-%m-%d'

    # Income vs Expenses Trend
    period_data = df.copy()
    period_data['period'] = period_data['date'].dt.strftime(date_format)
    income_expense = period_data.groupby(['period', 'transaction_type'])['amount'].sum().unstack()
    
    fig_trend = go.Figure()
    if 'Income' in income_expense.columns:
        fig_trend.add_trace(go.Bar(x=income_expense.index, y=income_expense['Income'],
                                 name='Income', marker_color='green'))
    if 'Expense' in income_expense.columns:
        fig_trend.add_trace(go.Bar(x=income_expense.index, y=-income_expense['Expense'],
                                 name='Expenses', marker_color='red'))
    
    fig_trend.update_layout(title=f'{selected_period} Income vs Expenses',
                          barmode='relative',
                          yaxis_title='Amount ($)')
    st.plotly_chart(fig_trend, use_container_width=True)

    # Category Analysis
    st.subheader("Category Analysis")
    
    expenses_only = df[df['transaction_type'] == 'Expense']
    
    tab1, tab2 = st.tabs(["Basic View", "Detailed View"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            category_expenses = expenses_only.groupby(['category name'])['amount'].sum().abs()
            fig_pie = px.pie(
                values=category_expenses.values,
                names=category_expenses.index,
                title='Expenses by Category'
            )
            st.plotly_chart(fig_pie)
        
        with col2:
            fig_bar = px.bar(
                category_expenses.reset_index().sort_values('amount', ascending=True).tail(10),
                x='amount', 
                y='category name',
                title='Top Spending Categories',
                orientation='h'
            )
            st.plotly_chart(fig_bar)
    
    with tab2:
        # Create sunburst chart
        category_data = expenses_only.groupby(
            ['category name', 'subcategory name']
        )['amount'].sum().abs().reset_index()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_sunburst = px.sunburst(
                category_data,
                path=['category name', 'subcategory name'],
                values='amount',
                title='Category and Subcategory Breakdown',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_sunburst.update_traces(textinfo="label+percent parent")
            st.plotly_chart(fig_sunburst, use_container_width=True)
        
        with col2:
            st.markdown("#### Top 10 Subcategories")
            subcategory_expenses = category_data.sort_values('amount', ascending=False).head(10)
            subcategory_expenses['amount'] = subcategory_expenses['amount'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(
                subcategory_expenses,
                column_config={
                    "category name": "Category",
                    "subcategory name": "Subcategory",
                    "amount": "Amount"
                },
                hide_index=True
            )

def main():
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file)
            # Store in session state for other pages
            st.session_state['data'] = df
            
            # Display summary metrics
            create_summary_metrics(df)
            
            # Create visualizations
            create_visualizations(df)
            
            # Show raw data if requested
            if st.checkbox("Show raw data"):
                st.write(df)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 