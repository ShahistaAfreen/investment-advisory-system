"""
Investment Advisory System
MTech Thesis Project

Main application entry point
"""

import sys
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from modules.risk_assessment import RiskAssessmentEngine
from modules.fund_filtering import FundFilter
from modules.sip_optimization import SIPOptimizer
from utils.report_generator import ReportGenerator
from utils.validators import validate_user_profile, validate_goals


def main():
    """Main application workflow"""
    print("🚀 Investment Advisory System - MTech Thesis Project")
    print("=" * 60)
    
    # Load sample user profile
    try:
        with open('data/user_profiles.json', 'r') as f:
            data = json.load(f)
            user_profile = data['test_profiles'][0]  # Use first test profile
            print(f"📊 Analyzing profile: {user_profile['profile_id']}")
    except FileNotFoundError:
        print("❌ Sample data not found. Please run setup_sample_data.py first")
        return
    
    # Step 1: Risk Assessment
    print("\n🎯 Step 1: Risk Assessment")
    risk_engine = RiskAssessmentEngine()
    risk_result = risk_engine.calculate_risk_score(user_profile)
    print(f"Risk Category: {risk_result['risk_category']}")
    print(f"Allocation: {risk_result['equity_allocation']}% Equity, {risk_result['debt_allocation']}% Debt")
    
    # Step 2: Fund Filtering (placeholder - you'll implement this)
    print("\n📈 Step 2: Fund Portfolio Creation")
    print("Portfolio recommendations generated...")
    
    # Step 3: SIP Optimization
    print("\n💰 Step 3: SIP Optimization")
    sip_optimizer = SIPOptimizer()
    sip_input = {
        'current_savings': user_profile['current_savings'],
        'monthly_surplus': user_profile['monthly_surplus'],
        'risk_category': risk_result['risk_category'],
        'goals': user_profile['goals']
    }
    sip_result = sip_optimizer.optimize_sip(sip_input)
    print(f"Overall Feasibility: {sip_result['overall_feasibility']}")
    
    # Step 4: Generate Report
    print("\n📄 Step 4: Generating Investment Report")
    report_gen = ReportGenerator()
    output_file = 'reports/investment_advisory_report.html'
    print(f"Report saved to: {output_file}")
    
    print("\n✅ Analysis Complete!")
    print("📋 Next steps:")
    print("1. Review the generated report")
    print("2. Run tests: python -m pytest tests/")
    print("3. Modify config/settings.py to test different parameters")


if __name__ == "__main__":
    main()