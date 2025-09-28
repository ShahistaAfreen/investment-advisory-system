"""
Fund Filtering Module
Investment Advisory System - MTech Thesis Project

Simple implementation for filtering and selecting optimal mutual funds
based on risk profile and fund performance metrics
"""

import pandas as pd
import numpy as np


def get_expense_threshold(category):
    """Get expense ratio threshold for different fund categories"""
    thresholds = {
        'large_cap': 2.0,
        'mid_cap': 2.25,
        'small_cap': 2.5,
        'debt': 1.5,
        'hybrid': 2.0
    }
    return thresholds.get(category, 2.0)  # default threshold


def apply_category_filters(category_funds, category):
    """Helper function to apply filters to a category"""
    return category_funds[
        (category_funds['3yr_return'] > category_funds['3yr_return'].quantile(0.5)) & # Filter for funds with above median 3-year return
        (category_funds['expense_ratio'] < get_expense_threshold(category)) &       # Filter for funds with expense ratio below a category-specific threshold
        # (category_funds['aum'] > 500) &                                              # Filter for funds with Assets Under Management (AUM) greater than 500 (likely in millions/crores)
        (category_funds['age_years'] > 3) &                                          # Filter for funds older than 3 years
        (category_funds['sharpe_ratio'] > category_funds['sharpe_ratio'].quantile(0.75)) # Filter for funds with Sharpe ratio above the 75th percentile
    ].copy()


def normalize(series):
    """Helper function to normalize a pandas series to 0-1 range"""
    min_val, max_val = series.min(), series.max()
    if max_val == min_val:
        return series * 0  # All values are the same
    return (series - min_val) / (max_val - min_val)


def get_top_funds(filtered_funds):
    """Helper function to score and select top funds"""
    filtered_funds['score'] = (
        0.4 * normalize(filtered_funds['3yr_return']) +
        0.2 * normalize(-filtered_funds['expense_ratio']) +  # lower is better
        0.2 * normalize(filtered_funds['sharpe_ratio']) +
        0.2 * normalize(filtered_funds['alpha'])
    )
    return filtered_funds.nlargest(5, 'score')


def get_risk_category_from_score(risk_score):
    """
    Convert risk score into granular categories + allocation
    (Same as risk_assessment module - could be imported instead)
    """
    if risk_score <= 0.2:
        return "Very Conservative", {"debt": 0.85, "equity": 0.15}
    elif risk_score <= 0.4:
        return "Conservative", {"debt": 0.70, "equity": 0.30}
    elif risk_score <= 0.6:
        return "Moderate", {"debt": 0.55, "equity": 0.45}
    elif risk_score <= 0.8:
        return "Growth", {"debt": 0.35, "equity": 0.65}
    else:
        return "Aggressive", {"debt": 0.20, "equity": 0.80}


def filter_funds(fund_universe, risk_score):
    """
    Filter funds based on category rules AND risk profile allocation.
    Returns only the categories matching the user's risk bucket with proper allocation.
    
    Args:
        fund_universe: DataFrame with fund data
        risk_score: Risk score between 0-1
    
    Returns:
        Tuple of (risk_category, filtered_funds_dict)
    """
    # 1. Get risk category + allocation
    risk_category, allocation = get_risk_category_from_score(risk_score)

    # 2. Define how to split equity allocation across sub-categories
    # These represent the proportion within the equity allocation
    equity_split = {
        "large_cap": 0.5,   # 50% of equity allocation
        "mid_cap": 0.3,     # 30% of equity allocation
        "small_cap": 0.2    # 20% of equity allocation
    }

    # 3. Define how to split debt allocation (currently 100% to debt category)
    debt_split = {
        "debt": 1.0   # 100% of debt allocation (can later split into subcategories)
    }

    filtered_funds = {}

    # 4. Process equity categories
    if allocation["equity"] > 0:
        for equity_category, split_pct in equity_split.items():
            category_funds = fund_universe[fund_universe['category'] == equity_category]
            if category_funds.empty:
                continue

            # Apply filters
            filtered = apply_category_filters(category_funds, equity_category)
            if filtered.empty:
                continue

            # Calculate composite score and get top funds
            top_funds = get_top_funds(filtered)

            # Calculate actual allocation percentage
            actual_allocation = allocation["equity"] * split_pct

            filtered_funds[equity_category] = {
                "allocation_pct": actual_allocation,
                "funds": top_funds
            }

    # 5. Process debt categories
    if allocation["debt"] > 0:
        for debt_category, split_pct in debt_split.items():
            category_funds = fund_universe[fund_universe['category'] == debt_category]
            if category_funds.empty:
                continue

            # Apply filters
            filtered = apply_category_filters(category_funds, debt_category)
            if filtered.empty:
                continue

            # Calculate composite score and get top funds
            top_funds = get_top_funds(filtered)

            # Calculate actual allocation percentage
            actual_allocation = allocation["debt"] * split_pct

            filtered_funds[debt_category] = {
                "allocation_pct": actual_allocation,
                "funds": top_funds
            }

    # 6. Process hybrid funds (only if both debt and equity are meaningful)
    if allocation["equity"] > 0.2 and allocation["debt"] > 0.2:
        category_funds = fund_universe[fund_universe['category'] == 'hybrid']
        if not category_funds.empty:
            filtered = apply_category_filters(category_funds, 'hybrid')
            if not filtered.empty:
                top_funds = get_top_funds(filtered)

                # Hybrid can replace some portion of both debt and equity
                # Option 1: Small fixed percentage
                hybrid_allocation = min(0.15, allocation["equity"] * 0.2, allocation["debt"] * 0.2)

                # Option 2: Or calculate based on risk profile
                # hybrid_allocation = 0.1 if risk_score <= 0.6 else 0.05

                filtered_funds['hybrid'] = {
                    "allocation_pct": hybrid_allocation,
                    "funds": top_funds
                }

    return risk_category, filtered_funds


def create_portfolio_recommendations(fund_universe, risk_score):
    """
    Complete portfolio creation function - wrapper around filter_funds with better output formatting
    
    Args:
        fund_universe: DataFrame with fund data
        risk_score: Risk score between 0-1
    
    Returns:
        Dictionary with portfolio recommendations
    """
    risk_category, filtered_funds = filter_funds(fund_universe, risk_score)
    
    # Format output for easier use
    portfolio = {
        'risk_category': risk_category,
        'risk_score': risk_score,
        'total_categories': len(filtered_funds),
        'recommendations': {}
    }
    
    total_allocation = 0
    for category, data in filtered_funds.items():
        allocation_pct = data['allocation_pct']
        funds = data['funds']
        
        portfolio['recommendations'][category] = {
            'allocation_percentage': round(allocation_pct * 100, 1),
            'fund_count': len(funds),
            'top_funds': funds[['fund_name', 'category', '3yr_return', 'expense_ratio', 'sharpe_ratio', 'score']].to_dict('records') if not funds.empty else []
        }
        
        total_allocation += allocation_pct
    
    portfolio['total_allocation'] = round(total_allocation * 100, 1)
    
    return portfolio


# Test the module if run directly
# if __name__ == "__main__":
#     print("📈 Fund Filtering Module - Testing")
#     print("=" * 50)
    
#     # Create sample fund data for testing
#     print("\n🔧 Creating sample fund universe...")
    
#     sample_funds = pd.DataFrame({
#         'fund_name': [
#             'HDFC Top 100 Fund', 'Axis Bluechip Fund', 'SBI Large Cap Fund',
#             'DSP Midcap Fund', 'HDFC Mid-Cap Opportunities', 'Kotak Emerging Equity',
#             'SBI Small Cap Fund', 'DSP Small Cap Fund', 'Axis Small Cap Fund',
#             'HDFC Corporate Bond', 'SBI Corporate Bond', 'Axis Corporate Debt',
#             'HDFC Balanced Advantage', 'ICICI Prudential Balanced'
#         ],
#         'category': [
#             'large_cap', 'large_cap', 'large_cap',
#             'mid_cap', 'mid_cap', 'mid_cap',
#             'small_cap', 'small_cap', 'small_cap',
#             'debt', 'debt', 'debt',
#             'hybrid', 'hybrid'
#         ],
#         '3yr_return': [12.5, 13.8, 11.2, 15.6, 16.8, 14.9, 18.2, 19.5, 17.8, 7.8, 8.1, 7.5, 10.2, 9.8],
#         'expense_ratio': [1.05, 1.15, 1.95, 1.89, 2.1, 1.75, 2.15, 2.05, 2.3, 0.45, 0.55, 0.48, 1.25, 1.35],
#         'sharpe_ratio': [0.85, 0.92, 0.78, 0.88, 0.95, 0.82, 0.75, 0.88, 0.72, 1.25, 1.18, 1.22, 0.95, 0.89],
#         'alpha': [2.1, 2.8, 1.5, 3.2, 3.8, 2.9, 4.1, 4.5, 3.7, 1.2, 1.4, 1.1, 2.2, 1.9],
#         'age_years': [15, 12, 20, 8, 10, 7, 6, 9, 5, 12, 18, 8, 14, 16]
#     })
    
#     print(f"Sample fund universe created with {len(sample_funds)} funds")
#     print(f"Categories: {sample_funds['category'].unique()}")
    
#     # Test different risk profiles
#     test_cases = [
#         {'risk_score': 0.3, 'profile': 'Conservative Investor'},
#         {'risk_score': 0.5, 'profile': 'Moderate Investor'},
#         {'risk_score': 0.8, 'profile': 'Growth Investor'}
#     ]
    
#     for test in test_cases:
#         print(f"\n📊 Testing: {test['profile']} (Risk Score: {test['risk_score']})")
#         print("-" * 60)
        
#         portfolio = create_portfolio_recommendations(sample_funds, test['risk_score'])
        
#         print(f"Risk Category: {portfolio['risk_category']}")
#         print(f"Total Allocation: {portfolio['total_allocation']}%")
#         print(f"Categories Selected: {portfolio['total_categories']}")
        
#         for category, details in portfolio['recommendations'].items():
#             print(f"\n  {category.upper()}:")
#             print(f"    Allocation: {details['allocation_percentage']}%")
#             print(f"    Funds Available: {details['fund_count']}")
            
#             if details['top_funds']:
#                 top_fund = details['top_funds'][0]  # Show top fund
#                 print(f"    Top Fund: {top_fund['fund_name']}")
#                 print(f"    3yr Return: {top_fund['3yr_return']}%")
#                 print(f"    Expense Ratio: {top_fund['expense_ratio']}%")
    
#     print("\n✅ Fund Filtering Module working correctly!")
#     print("\nUsage Examples:")
#     print("1. risk_category, filtered = filter_funds(fund_universe, risk_score)")
#     print("2. portfolio = create_portfolio_recommendations(fund_universe, risk_score)")