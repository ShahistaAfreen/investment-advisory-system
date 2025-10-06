"""
Investment Advisory System - Streamlit Web Application
MTech Thesis Project

Interactive web app for personalized investment recommendations
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import sys
import os

# Add modules to path
sys.path.append('modules')
from risk_assessment import analyze_user_risk_profile
from fund_filtering import create_portfolio_recommendations

# Configure Streamlit page
st.set_page_config(
    page_title="Investment Advisory System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .risk-conservative { border-left-color: #2ca02c; }
    .risk-moderate { border-left-color: #ff7f0e; }
    .risk-aggressive { border-left-color: #d62728; }
</style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data
def load_sample_fund_data():
    """Load sample mutual fund data"""
    return pd.DataFrame({
        'fund_name': [
            'HDFC Top 100 Fund', 'Axis Bluechip Fund', 'SBI Large Cap Fund', 'ICICI Prudential Bluechip',
            'DSP Midcap Fund', 'HDFC Mid-Cap Opportunities', 'Kotak Emerging Equity', 'Invesco India Midcap',
            'SBI Small Cap Fund', 'DSP Small Cap Fund', 'Axis Small Cap Fund', 'Nippon India Small Cap',
            'HDFC Corporate Bond', 'SBI Corporate Bond', 'Axis Corporate Debt', 'ICICI Prudential Corporate Bond',
            'HDFC Balanced Advantage', 'ICICI Prudential Balanced', 'SBI Equity Hybrid', 'Kotak Balanced'
        ],
        'category': [
            'large_cap', 'large_cap', 'large_cap', 'large_cap',
            'mid_cap', 'mid_cap', 'mid_cap', 'mid_cap', 
            'small_cap', 'small_cap', 'small_cap', 'small_cap',
            'debt', 'debt', 'debt', 'debt',
            'hybrid', 'hybrid', 'hybrid', 'hybrid'
        ],
        '3yr_return': [12.5, 13.8, 11.2, 12.8, 15.6, 16.8, 14.9, 15.2, 18.2, 19.5, 17.8, 18.9, 7.8, 8.1, 7.5, 7.9, 10.2, 9.8, 10.5, 9.5],
        'expense_ratio': [1.05, 1.15, 1.95, 1.25, 1.89, 2.1, 1.75, 1.95, 2.15, 2.05, 2.3, 2.2, 0.45, 0.55, 0.48, 0.52, 1.25, 1.35, 1.45, 1.38],
        'sharpe_ratio': [0.85, 0.92, 0.78, 0.88, 0.88, 0.95, 0.82, 0.89, 0.75, 0.88, 0.72, 0.85, 1.25, 1.18, 1.22, 1.20, 0.95, 0.89, 0.92, 0.87],
        'alpha': [2.1, 2.8, 1.5, 2.3, 3.2, 3.8, 2.9, 3.1, 4.1, 4.5, 3.7, 4.2, 1.2, 1.4, 1.1, 1.3, 2.2, 1.9, 2.4, 1.8],
        'age_years': [15, 12, 20, 18, 8, 10, 7, 9, 6, 9, 5, 7, 12, 18, 8, 14, 14, 16, 11, 13]
    })

def calculate_sip_projection(monthly_sip, years, annual_return):
    """Calculate SIP projection over time"""
    months = years * 12
    monthly_return = annual_return / 12
    
    projections = []
    total_invested = 0
    maturity_value = 0
    
    for month in range(1, months + 1):
        total_invested = month * monthly_sip
        # SIP future value formula
        if monthly_return > 0:
            maturity_value = monthly_sip * (((1 + monthly_return) ** month - 1) / monthly_return) * (1 + monthly_return)
        else:
            maturity_value = total_invested
            
        projections.append({
            'Month': month,
            'Year': month / 12,
            'Total Invested': total_invested,
            'Maturity Value': maturity_value,
            'Gains': maturity_value - total_invested
        })
    
    return pd.DataFrame(projections)

def monte_carlo_simulation(monthly_sip, years, expected_return, volatility, target_amount, simulations=1000):
    """Run Monte Carlo simulation for goal achievement probability"""
    months = years * 12
    results = []
    
    for _ in range(simulations):
        portfolio_value = 0
        monthly_return = expected_return / 12
        monthly_volatility = volatility / math.sqrt(12)
        
        for month in range(months):
            # Random return for this month
            random_return = np.random.normal(monthly_return, monthly_volatility)
            # Add monthly SIP and apply return
            portfolio_value = (portfolio_value + monthly_sip) * (1 + random_return)
        
        results.append(portfolio_value)
    
    results = np.array(results)
    success_rate = (results >= target_amount).mean() * 100
    
    return results, success_rate

# Main App
def main():
    # Header
    st.markdown('<h1 class="main-header">💰 Investment Advisory System</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Personalized Mutual Fund Recommendations & SIP Planning</p>', unsafe_allow_html=True)
    
    # Load fund data
    fund_universe = load_sample_fund_data()
    
    # Sidebar for inputs
    st.sidebar.header("📝 Your Financial Profile")
    
    # Personal Information
    st.sidebar.subheader("Personal Details")
    age = st.sidebar.slider("Age", 18, 65, 30)
    monthly_income = st.sidebar.number_input("Monthly Income (₹)", 20000, 500000, 75000, step=5000)
    
    # Financial Information  
    st.sidebar.subheader("Financial Details")
    current_savings = st.sidebar.number_input("Current Savings (₹)", 0, 5000000, 200000, step=10000)
    monthly_surplus = st.sidebar.number_input("Monthly Investment Surplus (₹)", 1000, 100000, 15000, step=1000)
    
    # Risk Tolerance
    st.sidebar.subheader("Risk Assessment")
    risk_tolerance = st.sidebar.slider("Risk Tolerance (1=Conservative, 10=Aggressive)", 1, 10, 5)
    
    # Financial Goals
    st.sidebar.subheader("Financial Goals")
    goal_1_years = st.sidebar.selectbox("Goal 1 Timeline", [3, 5, 7, 10, 15, 20], index=1)
    goal_1_amount = st.sidebar.number_input(f"Goal 1 Target Amount (₹) - {goal_1_years} years", 100000, 10000000, 500000, step=50000)
    
    goal_2_years = st.sidebar.selectbox("Goal 2 Timeline", [5, 10, 15, 20, 25], index=2)
    goal_2_amount = st.sidebar.number_input(f"Goal 2 Target Amount (₹) - {goal_2_years} years", 200000, 20000000, 1000000, step=100000)
    
    # Process button
    if st.sidebar.button("🚀 Get Investment Recommendations", type="primary"):
        # Prepare user data
        user_data = {
            'age': age,
            'income': monthly_income,
            'current_savings': current_savings,
            'monthly_surplus': monthly_surplus,
            'goals': {goal_1_years * 12: goal_1_amount, goal_2_years * 12: goal_2_amount},
            'risk_tolerance': risk_tolerance
        }
        
        # Store in session state
        st.session_state['user_data'] = user_data
        st.session_state['analysis_done'] = True
    
    # Main content area
    if 'analysis_done' in st.session_state and st.session_state['analysis_done']:
        user_data = st.session_state['user_data']
        
        # Risk Assessment
        st.markdown('<h2 class="sub-header">🎯 Risk Assessment Results</h2>', unsafe_allow_html=True)
        
        risk_result = analyze_user_risk_profile(user_data)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Risk Score", f"{risk_result['risk_score']}", help="Risk score from 0 (Conservative) to 1 (Aggressive)")
        
        with col2:
            st.metric("Risk Category", risk_result['risk_category'])
        
        with col3:
            st.metric("Equity Allocation", f"{risk_result['equity_percentage']}%")
        
        with col4:
            st.metric("Debt Allocation", f"{risk_result['debt_percentage']}%")
        
        # Portfolio Recommendations
        st.markdown('<h2 class="sub-header">📈 Recommended Portfolio</h2>', unsafe_allow_html=True)
        
        portfolio = create_portfolio_recommendations(fund_universe, risk_result['risk_score'])
        
        # Portfolio Allocation Chart
        if portfolio['recommendations']:
            categories = []
            allocations = []
            colors = {'large_cap': '#1f77b4', 'mid_cap': '#ff7f0e', 'small_cap': '#2ca02c', 
                     'debt': '#d62728', 'hybrid': '#9467bd'}
            
            for category, details in portfolio['recommendations'].items():
                categories.append(category.replace('_', ' ').title())
                allocations.append(details['allocation_percentage'])
            
            fig_pie = px.pie(values=allocations, names=categories, 
                           title="Portfolio Allocation",
                           color_discrete_sequence=[colors.get(cat.lower().replace(' ', '_'), '#grey') for cat in categories])
            
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Fund Recommendations
        st.markdown('<h2 class="sub-header">🏆 Top Fund Recommendations</h2>', unsafe_allow_html=True)
        
        for category, details in portfolio['recommendations'].items():
            if details['top_funds']:
                st.subheader(f"{category.replace('_', ' ').title()} Funds - {details['allocation_percentage']}% Allocation")
                
                # Create DataFrame for display
                funds_df = pd.DataFrame(details['top_funds'])
                funds_display = funds_df[['fund_name', '3yr_return', 'expense_ratio', 'sharpe_ratio']].copy()
                funds_display.columns = ['Fund Name', '3-Year Return (%)', 'Expense Ratio (%)', 'Sharpe Ratio']
                funds_display['3-Year Return (%)'] = funds_display['3-Year Return (%)'].round(1)
                funds_display['Expense Ratio (%)'] = funds_display['Expense Ratio (%)'].round(2)
                funds_display['Sharpe Ratio'] = funds_display['Sharpe Ratio'].round(2)
                
                st.dataframe(funds_display, use_container_width=True, hide_index=True)
        
        # SIP Analysis and Projections
        st.markdown('<h2 class="sub-header">💹 SIP Analysis & Projections</h2>', unsafe_allow_html=True)
        
        # Expected returns based on risk category
        expected_returns = {
            'Very Conservative': 0.08, 'Conservative': 0.10, 'Moderate': 0.12, 
            'Growth': 0.14, 'Aggressive': 0.16
        }
        expected_return = expected_returns.get(risk_result['risk_category'], 0.12)
        
        # Calculate required SIP for goals
        goals_analysis = []
        for goal_months, goal_amount in user_data['goals'].items():
            goal_years = goal_months // 12
            
            # SIP calculation
            monthly_rate = expected_return / 12
            required_sip = goal_amount * monthly_rate / ((1 + monthly_rate) ** goal_months - 1)
            
            goals_analysis.append({
                'Goal': f'Goal {len(goals_analysis) + 1}',
                'Timeline': f'{goal_years} years',
                'Target Amount': f'₹{goal_amount:,}',
                'Required SIP': f'₹{required_sip:,.0f}',
                'Feasibility': 'Feasible' if required_sip <= monthly_surplus else 'Challenging'
            })
        
        # Display goals analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Goal Analysis")
            goals_df = pd.DataFrame(goals_analysis)
            st.dataframe(goals_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("📊 Investment Capacity")
            total_required = sum([float(goal['Required SIP'].replace('₹', '').replace(',', '')) for goal in goals_analysis])
            
            st.metric("Total Required SIP", f"₹{total_required:,.0f}")
            st.metric("Available Surplus", f"₹{monthly_surplus:,}")
            utilization = (total_required / monthly_surplus) * 100 if monthly_surplus > 0 else 0
            st.metric("Surplus Utilization", f"{utilization:.1f}%")
        
        # SIP Projections
        st.markdown('<h2 class="sub-header">📈 SIP Growth Projections</h2>', unsafe_allow_html=True)
        
        # Use the first goal for projection
        first_goal_months = list(user_data['goals'].keys())[0]
        first_goal_amount = list(user_data['goals'].values())[0]
        projection_years = first_goal_months // 12
        
        suggested_sip = min(monthly_surplus * 0.8, float(goals_analysis[0]['Required SIP'].replace('₹', '').replace(',', '')))
        
        projection_data = calculate_sip_projection(suggested_sip, projection_years, expected_return)
        
        # Create projection chart
        fig_projection = go.Figure()
        
        fig_projection.add_trace(go.Scatter(
            x=projection_data['Year'], 
            y=projection_data['Total Invested'],
            mode='lines', 
            name='Total Invested',
            line=dict(color='#ff7f0e', width=3)
        ))
        
        fig_projection.add_trace(go.Scatter(
            x=projection_data['Year'], 
            y=projection_data['Maturity Value'],
            mode='lines', 
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=3)
        ))
        
        # Add target line
        fig_projection.add_hline(y=first_goal_amount, line_dash="dash", line_color="red", 
                                annotation_text=f"Target: ₹{first_goal_amount:,}")
        
        fig_projection.update_layout(
            title=f'SIP Growth Projection - ₹{suggested_sip:,.0f} Monthly for {projection_years} Years',
            xaxis_title='Years',
            yaxis_title='Amount (₹)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_projection, use_container_width=True)
        
        # Monte Carlo Simulation
        st.markdown('<h2 class="sub-header">🎲 Goal Achievement Probability</h2>', unsafe_allow_html=True)
        
        volatility = 0.15  # Assume 15% annual volatility
        simulation_results, success_rate = monte_carlo_simulation(
            suggested_sip, projection_years, expected_return, volatility, first_goal_amount
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Success probability
            st.metric("Goal Achievement Probability", f"{success_rate:.1f}%")
            
            # Risk metrics
            median_value = np.median(simulation_results)
            percentile_10 = np.percentile(simulation_results, 10)
            percentile_90 = np.percentile(simulation_results, 90)
            
            st.metric("Median Portfolio Value", f"₹{median_value:,.0f}")
            st.metric("10th Percentile (Worst Case)", f"₹{percentile_10:,.0f}")
            st.metric("90th Percentile (Best Case)", f"₹{percentile_90:,.0f}")
        
        with col2:
            # Distribution chart
            fig_hist = px.histogram(
                x=simulation_results, 
                nbins=50, 
                title=f'Portfolio Value Distribution After {projection_years} Years'
            )
            
            fig_hist.add_vline(x=first_goal_amount, line_dash="dash", line_color="red", 
                              annotation_text=f"Target: ₹{first_goal_amount:,}")
            fig_hist.add_vline(x=median_value, line_dash="dot", line_color="green", 
                              annotation_text=f"Median: ₹{median_value:,}")
            
            fig_hist.update_layout(
                xaxis_title='Portfolio Value (₹)',
                yaxis_title='Frequency',
                showlegend=False
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
        
        # Action Items
        st.markdown('<h2 class="sub-header">✅ Recommended Actions</h2>', unsafe_allow_html=True)
        
        recommendations = []
        
        if utilization <= 70:
            recommendations.append("✅ Your goals are easily achievable with current surplus")
        elif utilization <= 90:
            recommendations.append("⚠️ Goals are challenging but achievable - consider optimizing expenses")
        else:
            recommendations.append("❌ Goals may require higher income or extended timeline")
        
        if success_rate >= 80:
            recommendations.append("✅ High probability of achieving your financial goals")
        elif success_rate >= 60:
            recommendations.append("⚠️ Moderate success probability - consider risk adjustment")
        else:
            recommendations.append("❌ Low success probability - review goals or investment strategy")
        
        recommendations.append(f"💡 Start with ₹{suggested_sip:,.0f} monthly SIP in recommended funds")
        recommendations.append("📊 Review and rebalance portfolio annually")
        recommendations.append("📈 Consider increasing SIP by 10% annually with salary increments")
        
        for rec in recommendations:
            st.write(rec)
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to Your Personal Investment Advisory System! 👋
        
        This system will help you:
        - 🎯 Assess your risk profile based on financial situation
        - 📈 Recommend optimal mutual funds for your portfolio  
        - 💰 Calculate required SIP amounts for your goals
        - 📊 Project portfolio growth over time
        - 🎲 Analyze probability of achieving financial goals
        
        **Get started by filling out your financial profile in the sidebar** ➡️
        """)
        
        # Show sample charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Sample risk distribution
            sample_risk = pd.DataFrame({
                'Risk Category': ['Very Conservative', 'Conservative', 'Moderate', 'Growth', 'Aggressive'],
                'Users': [15, 25, 35, 20, 5]
            })
            fig = px.pie(sample_risk, values='Users', names='Risk Category', title='Risk Profile Distribution')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Sample growth projection
            years = np.arange(1, 21)
            sample_growth = 10000 * (1.12 ** years)  # 12% annual growth
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=years, y=sample_growth, mode='lines', name='Portfolio Growth'))
            fig2.update_layout(title='Sample SIP Growth (₹10,000/month @ 12% return)', 
                             xaxis_title='Years', yaxis_title='Portfolio Value (₹)')
            st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()