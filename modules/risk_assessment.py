"""
Risk Assessment Module
Investment Advisory System - MTech Thesis Project

Simple and clean implementation of risk assessment logic
Based on 6-factor analysis with configurable weights
"""

import numpy as np
import math


def calculate_risk_score(
    age, income, current_savings, monthly_surplus, goals,
    risk_tolerance=3,   # from questionnaire: 1 (low) – 5 (high)
    weights=None        # user can supply custom weights
):
    """
    Calculate risk score with configurable weights, risk tolerance,
    capped income normalization, and goals dict (month: target).

    Args:
        age: User's age in years
        income: Monthly income in rupees
        current_savings: Total current savings in rupees
        monthly_surplus: Available monthly surplus for investment
        goals: Dictionary of {months: target_amount} for financial goals
        risk_tolerance: Risk tolerance score from 1 (low) to 5 (high)
        weights: Optional custom weights for factors

    Returns: 
        Risk score between 0-1
    """

    # Default weights (can be overridden by user)
    default_weights = {
        "age": 0.25,
        "income": 0.20,
        "timeline": 0.20,
        "surplus": 0.15,
        "savings": 0.10,
        "tolerance": 0.10
    }
    w = weights if weights else default_weights

    # --- 1. Age Factor ---
    if age <= 25:
        age_factor = 1.0
    elif age <= 35:
        age_factor = 0.8
    elif age <= 45:
        age_factor = 0.6
    elif age <= 55:
        age_factor = 0.4
    else:
        age_factor = 0.2

    # --- 2. Income Factor (cap at ₹1L/month) ---
    capped_income = min(income, 100000)
    income_factor = capped_income / 100000  # simple normalization
    income_factor = min(max(income_factor, 0), 1)

    # --- 3. Surplus Factor (log scale) that is scaled relative to the user's income---
    surplus = max(monthly_surplus, 0)
    surplus_factor = math.log1p(surplus) / math.log1p(income/2 if income > 0 else 1)
    surplus_factor = min(max(surplus_factor, 0), 1)

    # --- 4. Savings Factor ---
    monthly_income = income / 12 if income > 0 else 1
    savings_months = current_savings / monthly_income
    savings_factor = math.log1p(savings_months) / math.log1p(60)  # cap at 5 years
    savings_factor = min(max(savings_factor, 0), 1)

    # --- 5. Timeline Factor (from goals dict {month: target}) ---
    if goals and len(goals) > 0:
        avg_timeline_years = np.mean([months/12 for months in goals.keys()])
        timeline_factor = math.log1p(avg_timeline_years) / math.log1p(30)  # cap at 30 years
        timeline_factor = min(max(timeline_factor, 0), 1)
    else:
        timeline_factor = 0.5

    # --- 6. Risk Tolerance (from questionnaire 1–5) ---
    tolerance_factor = (risk_tolerance - 1) / 4  # normalize 1→0, 5→1

    # --- Weighted Risk Score ---
    risk_score = (
        w["age"] * age_factor +
        w["income"] * income_factor +
        w["timeline"] * timeline_factor +
        w["surplus"] * surplus_factor +
        w["savings"] * savings_factor +
        w["tolerance"] * tolerance_factor
    )

    return min(max(risk_score, 0), 1)


def get_risk_category_from_score(risk_score):
    """
    Convert risk score into granular categories + allocation
    
    Args:
        risk_score: Risk score between 0-1
    
    Returns:
        Tuple of (risk_category, allocation_dict)
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


def analyze_user_risk_profile(user_data):
    """
    Complete risk analysis for a user - combines both functions
    
    Args:
        user_data: Dictionary with user information
                  Required: age, income, current_savings, monthly_surplus, goals
                  Optional: risk_tolerance, custom_weights
    
    Returns:
        Dictionary with complete risk analysis
    """
    # Extract data with defaults
    age = user_data.get('age')
    income = user_data.get('income') 
    current_savings = user_data.get('current_savings')
    monthly_surplus = user_data.get('monthly_surplus')
    goals = user_data.get('goals', {})
    risk_tolerance = user_data.get('risk_tolerance', 3)
    custom_weights = user_data.get('weights')
    
    # Calculate risk score
    risk_score = calculate_risk_score(
        age, income, current_savings, monthly_surplus, goals,
        risk_tolerance, custom_weights
    )
    
    # Get category and allocation
    category, allocation = get_risk_category_from_score(risk_score)
    
    # Return comprehensive result
    return {
        'risk_score': round(risk_score, 3),
        'risk_category': category,
        'debt_percentage': round(allocation['debt'] * 100, 1),
        'equity_percentage': round(allocation['equity'] * 100, 1),
        'allocation': allocation
    }


# Test the module if run directly
# if __name__ == "__main__":
#     print("🎯 Risk Assessment Module - Testing")
#     print("=" * 50)
    
#     # Test case 1: Young aggressive investor
#     print("\n📊 Test Case 1: Young Aggressive Investor")
#     young_investor = {
#         'age': 25,
#         'income': 80000,
#         'current_savings': 200000,
#         'monthly_surplus': 25000,
#         'goals': {60: 500000, 120: 1000000},  # 5 and 10 year goals
#         'risk_tolerance': 5
#     }
    
#     result1 = analyze_user_risk_profile(young_investor)
#     print(f"Risk Score: {result1['risk_score']}")
#     print(f"Category: {result1['risk_category']}")
#     print(f"Allocation: {result1['equity_percentage']}% Equity, {result1['debt_percentage']}% Debt")
    
#     # Test case 2: Conservative older investor
#     print("\n📊 Test Case 2: Conservative Older Investor")
#     older_investor = {
#         'age': 55,
#         'income': 120000,
#         'current_savings': 1500000,
#         'monthly_surplus': 20000,
#         'goals': {36: 300000},  # 3 year goal
#         'risk_tolerance': 2
#     }
    
#     result2 = analyze_user_risk_profile(older_investor)
#     print(f"Risk Score: {result2['risk_score']}")
#     print(f"Category: {result2['risk_category']}")
#     print(f"Allocation: {result2['equity_percentage']}% Equity, {result2['debt_percentage']}% Debt")
    
#     # Test case 3: Custom weights example
#     print("\n📊 Test Case 3: Custom Weights (Higher Age Importance)")
#     custom_weights_test = young_investor.copy()
#     custom_weights_test['weights'] = {
#         "age": 0.40,        # Increased age importance
#         "income": 0.15,
#         "timeline": 0.15,
#         "surplus": 0.10,
#         "savings": 0.10,
#         "tolerance": 0.10
#     }
    
#     result3 = analyze_user_risk_profile(custom_weights_test)
#     print(f"Risk Score: {result3['risk_score']} (vs {result1['risk_score']} with default weights)")
#     print(f"Category: {result3['risk_category']}")
    
#     print("\n✅ Risk Assessment Module working correctly!")
#     print("\nUsage Examples:")
#     print("1. risk_score = calculate_risk_score(age, income, savings, surplus, goals)")
#     print("2. category, allocation = get_risk_category_from_score(risk_score)")
#     print("3. full_analysis = analyze_user_risk_profile(user_data_dict)")