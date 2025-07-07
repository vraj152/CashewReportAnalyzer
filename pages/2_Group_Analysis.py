import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_plotly_events import plotly_events

# Set page config
st.set_page_config(
    page_title="Group Analysis",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"  # This ensures sidebar starts expanded
)

# Add sidebar title for better visibility
st.sidebar.title("Navigation")
st.sidebar.markdown("👆 Use the menu above to navigate between pages")

# Title and description
st.title("🏷️ Group Analysis")
st.markdown("""
Analyze your expenses by groups/tags. Select multiple groups to compare their expenses and patterns.
""")

def extract_hashtags(note):
    if pd.isna(note):
        return []
    tags = []
    notes = str(note).split("\n")
    for note in notes:
        if note.startswith('#'):
            note = note.replace('#', '')
            tag = ' '.join(word.capitalize() for word in note.split())
            tags.append(tag)
    return tags

def load_data():
    try:
        # Try to get data from session state
        return st.session_state['data']
    except KeyError:
        # If not in session state, load sample data
        df = pd.read_csv("data/CashewReport_CashewData.csv")
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = df['amount'].astype(float)
        df['transaction_type'] = df['income'].map({True: 'Income', False: 'Expense'})
        df['hashtags'] = df['note'].apply(extract_hashtags)
        return df

# Load data
df = load_data()

def analyze_groups(df):
    # Get all unique hashtags
    all_hashtags = sorted(set([tag for tags in df['hashtags'] for tag in tags]))
    
    if all_hashtags:
        st.write(f"Found {len(all_hashtags)} groups in your data")
        selected_groups = st.multiselect('Select Groups to Compare', all_hashtags)
        
        if selected_groups:
            # Create group summary
            group_data = []
            for group in selected_groups:
                group_expenses = df[df['hashtags'].apply(lambda x: group in x)]
                group_expenses_only = group_expenses[group_expenses['transaction_type'] == 'Expense']
                
                group_data.append({
                    'Group': group,
                    'Total Spent': abs(group_expenses_only['amount'].sum()),
                    'Duration': (group_expenses['date'].max() - group_expenses['date'].min()).days + 1,
                    'Top Category': group_expenses_only.groupby(['category name'])['amount'].sum().abs().idxmax(),
                    'Transactions': len(group_expenses_only)
                })
            
            group_df = pd.DataFrame(group_data)
            
            # Display group comparison
            col1, col2 = st.columns(2)
            
            with col1:
                fig_group_expenses = px.bar(group_df, 
                                          x='Group', y='Total Spent',
                                          title='Group Expenses Comparison',
                                          labels={'Total Spent': 'Total Spent ($)'})
                fig_group_expenses.update_traces(marker_color='indianred')
                st.plotly_chart(fig_group_expenses)
            
            with col2:
                # Show group details in a table
                st.write("Group Details:")
                st.dataframe(group_df.set_index('Group').style.format({
                    'Total Spent': '${:,.2f}',
                    'Duration': '{} days'
                }))
            
            # Show category breakdown for selected groups
            st.subheader("Category Breakdown by Group")
            
            # Prepare category data
            category_data = []
            for group in selected_groups:
                group_expenses = df[df['hashtags'].apply(lambda x: group in x)]
                group_expenses = group_expenses[group_expenses['transaction_type'] == 'Expense']
                
                for _, row in group_expenses.iterrows():
                    category_data.append({
                        'Category': row['category name'],
                        'Group': group,
                        'Amount': abs(row['amount'])
                    })
            
            category_df = pd.DataFrame(category_data)
            category_pivot = category_df.pivot_table(
                values='Amount',
                index='Category',
                columns='Group',
                aggfunc='sum'
            ).fillna(0)
            
            # Create the clickable chart
            fig_category = px.bar(category_pivot,
                                title='Category-wise Expenses by Group',
                                barmode='group',
                                labels={'value': 'Amount ($)'},
                                color_discrete_sequence=['indianred', 'royalblue', 'green', 'orange', 'purple'])  # Add more colors if needed
            
            # Customize layout for better readability
            fig_category.update_layout(
                showlegend=True,
                legend_title_text='Groups',
                bargap=0.2,  # Gap between bars in the same group
                bargroupgap=0.1  # Gap between bar groups
            )
            
            # Only show one chart with click events enabled
            selected_point = plotly_events(fig_category, override_height=600)
            
            # Show transactions if a category is clicked
            if selected_point:
                selected_category = selected_point[0]['x']
                st.markdown(f"#### Transactions for {selected_category}")
                
                # Create tabs for each selected group
                group_tabs = st.tabs(selected_groups)
                
                for group, tab in zip(selected_groups, group_tabs):
                    with tab:
                        # Get transactions for this specific group and category
                        group_transactions = df[
                            (df['category name'] == selected_category) & 
                            (df['hashtags'].apply(lambda x: group in x)) &
                            (df['transaction_type'] == 'Expense')
                        ][['date', 'title', 'subcategory name', 'amount', 'note']].copy()
                        
                        # Clean notes: remove lines with hashtags
                        def clean_note(note):
                            if pd.isna(note):
                                return ""
                            return "\n".join(line for line in str(note).split('\n') 
                                           if not line.strip().startswith('#')).strip()
                        
                        group_transactions['note'] = group_transactions['note'].apply(clean_note)
                        
                        # Sort and format
                        group_transactions = group_transactions.sort_values('amount', ascending=False)
                        group_transactions['date'] = group_transactions['date'].dt.strftime('%Y-%m-%d')
                        group_transactions['amount'] = group_transactions['amount'].abs().apply(lambda x: f"${x:,.2f}")
                        
                        # Show total for this group/category
                        total = df[
                            (df['category name'] == selected_category) & 
                            (df['hashtags'].apply(lambda x: group in x)) &
                            (df['transaction_type'] == 'Expense')
                        ]['amount'].abs().sum()
                        
                        st.metric("Total", f"${total:,.2f}")
                        
                        # Show transactions table
                        st.dataframe(
                            group_transactions,
                            column_config={
                                "date": {
                                    "label": "Date",
                                    "width": 90
                                },
                                "title": {
                                    "label": "Description",
                                    "width": 150
                                },
                                "subcategory name": {
                                    "label": "Subcategory",
                                    "width": 120
                                },
                                "amount": {
                                    "label": "Amount",
                                    "width": 90
                                },
                                "note": {
                                    "label": "Note"
                                }
                            },
                            hide_index=True,
                            use_container_width=True
                        )
    else:
        st.info("No groups found in the data. Make sure your notes contain hashtags.")

# Main execution
analyze_groups(df) 