"""
Risk Assessment Engine Module
Investment Advisory System - MTech Thesis Project

This module calculates personalized risk scores based on multiple financial factors
and determines appropriate asset allocation strategies.

Author: Afreen
"""

import math
import os
import sys
import numpy as np
from typing import Dict, Optional, Tuple, Union
import logging
# from config.settings import RiskAssessmentConfig, AllocationConfig -> If using this use command : python -m modules.risk_assessment

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from config.settings import RiskAssessmentConfig, AllocationConfig
#  Command : python -m modules.risk_assessment


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskAssessmentEngine:
    """
    Advanced Risk Assessment Engine for Investment Advisory System
    
    Calculates personalized risk scores using multi-factor analysis:
    - Age factor (investment horizon)
    - Income level (risk capacity)
    - Investment timeline (goal duration)
    - Monthly surplus (investment capability)
    - Current savings (financial cushion)
    - Risk tolerance (subjective preference)
    """
    
    def __init__(self, config: Optional[RiskAssessmentConfig] = None):
        """
        Initialize Risk Assessment Engine
        
        Args:
            config: Configuration object with weights and parameters
        """
        self.config = config or RiskAssessmentConfig()
        self.allocation_config = AllocationConfig()
        
        # Validate configuration
        self._validate_config()
        
        logger.info("Risk Assessment Engine initialized successfully")
    
    def _validate_config(self) -> None:
        """Validate configuration parameters"""
        total_weight = sum(self.config.WEIGHTS.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def calculate_risk_score(self, user_profile: Dict) -> Dict[str, Union[float, str, int]]:
        """
        Calculate comprehensive risk score for a user profile
        
        Args:
            user_profile: Dictionary containing user financial information
                Required keys: age, monthly_income, current_savings, monthly_surplus
                Optional keys: goals, risk_tolerance_score, custom_weights
        
        Returns:
            Dictionary with risk score, category, and allocation recommendations
        """
        try:
            # Extract and validate input parameters
            age = self._validate_age(user_profile.get('age', 30))
            income = self._validate_income(user_profile.get('monthly_income', 50000))
            current_savings = max(user_profile.get('current_savings', 0), 0)
            monthly_surplus = max(user_profile.get('monthly_surplus', 0), 0)
            goals = user_profile.get('goals', {})
            risk_tolerance = self._validate_risk_tolerance(
                user_profile.get('risk_tolerance_score', 5)
            )
            
            # Use custom weights if provided, otherwise use default
            weights = user_profile.get('custom_weights', self.config.WEIGHTS)
            
            # Calculate individual risk factors
            age_factor = self._calculate_age_factor(age)
            income_factor = self._calculate_income_factor(income)
            timeline_factor = self._calculate_timeline_factor(goals)
            surplus_factor = self._calculate_surplus_factor(monthly_surplus, income)
            savings_factor = self._calculate_savings_factor(current_savings, income)
            tolerance_factor = self._calculate_tolerance_factor(risk_tolerance)
            
            # Calculate weighted risk score
            risk_score = self._calculate_weighted_score(
                weights, age_factor, income_factor, timeline_factor,
                surplus_factor, savings_factor, tolerance_factor
            )
            
            # Determine risk category and allocation
            risk_category, allocation = self._get_risk_category_and_allocation(risk_score)
            
            # Log calculation details
            logger.info(f"Risk assessment completed - Score: {risk_score:.3f}, Category: {risk_category}")
            
            return {
                'risk_score': round(risk_score, 3),
                'risk_category': risk_category,
                'debt_allocation': allocation['debt'],
                'equity_allocation': allocation['equity'],
                'factor_breakdown': {
                    'age_factor': round(age_factor, 3),
                    'income_factor': round(income_factor, 3),
                    'timeline_factor': round(timeline_factor, 3),
                    'surplus_factor': round(surplus_factor, 3),
                    'savings_factor': round(savings_factor, 3),
                    'tolerance_factor': round(tolerance_factor, 3)
                },
                'weighted_contributions': {
                    'age_contribution': round(weights['age_factor'] * age_factor, 3),
                    'income_contribution': round(weights['income_factor'] * income_factor, 3),
                    'timeline_contribution': round(weights['timeline_factor'] * timeline_factor, 3),
                    'surplus_contribution': round(weights['surplus_factor'] * surplus_factor, 3),
                    'savings_contribution': round(weights['savings_factor'] * savings_factor, 3),
                    'tolerance_contribution': round(weights['risk_tolerance_factor'] * tolerance_factor, 3)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in risk assessment calculation: {str(e)}")
            # Return conservative default in case of error
            return self._get_default_conservative_profile()
    
    def _calculate_age_factor(self, age: int) -> float:
        """
        Calculate age-based risk factor
        Younger investors can take higher risk due to longer investment horizon
        """
        if age <= 25:
            return 1.0
        elif age <= 35:
            return 0.8
        elif age <= 45:
            return 0.6
        elif age <= 55:
            return 0.4
        else:
            return 0.2
    
    def _calculate_income_factor(self, income: float) -> float:
        """
        Calculate income-based risk factor with capping
        Higher income allows for greater risk tolerance
        """
        # Cap income at configured maximum to prevent skewing
        capped_income = min(income, self.config.INCOME_CAP)
        income_factor = capped_income / self.config.INCOME_CAP
        return min(max(income_factor, 0), 1)
    
    def _calculate_timeline_factor(self, goals: Dict[int, float]) -> float:
        """
        Calculate timeline-based risk factor from investment goals
        Longer investment horizons support higher risk strategies
        """
        if not goals or len(goals) == 0:
            return 0.5  # Default moderate timeline
        
        # Calculate average timeline in years
        avg_timeline_years = np.mean([months/12 for months in goals.keys()])
        
        # Use logarithmic scaling capped at 30 years
        timeline_factor = math.log1p(avg_timeline_years) / math.log1p(30)
        return min(max(timeline_factor, 0), 1)
    
    def _calculate_surplus_factor(self, monthly_surplus: float, income: float) -> float:
        """
        Calculate surplus-based risk factor using logarithmic scaling
        More surplus relative to income enables aggressive investing
        """
        if income <= 0:
            return 0.0
        
        surplus = max(monthly_surplus, 0)
        # Scale relative to half of income as reference point
        reference_income = income / 2 if income > 0 else 1
        surplus_factor = math.log1p(surplus) / math.log1p(reference_income)
        return min(max(surplus_factor, 0), 1)
    
    def _calculate_savings_factor(self, current_savings: float, monthly_income: float) -> float:
        """
        Calculate savings-based risk factor
        Higher savings provide cushion for risk-taking
        """
        if monthly_income <= 0:
            return 0.0
        
        # Calculate savings in terms of months of income
        savings_months = current_savings / monthly_income
        
        # Use logarithmic scaling capped at 60 months (5 years)
        savings_factor = math.log1p(savings_months) / math.log1p(60)
        return min(max(savings_factor, 0), 1)
    
    def _calculate_tolerance_factor(self, risk_tolerance: int) -> float:
        """
        Calculate risk tolerance factor from questionnaire
        Direct conversion from 1-10 scale to 0-1 factor
        """
        # Normalize from 1-10 scale to 0-1
        return (risk_tolerance - 1) / 9
    
    def _calculate_weighted_score(self, weights: Dict, *factors) -> float:
        """Calculate final weighted risk score"""
        factor_names = ['age_factor', 'income_factor', 'timeline_factor', 
                       'surplus_factor', 'savings_factor', 'risk_tolerance_factor']
        
        risk_score = sum(weights[name] * factor 
                        for name, factor in zip(factor_names, factors))
        
        return min(max(risk_score, 0), 1)
    
    def _get_risk_category_and_allocation(self, risk_score: float) -> Tuple[str, Dict[str, int]]:
        """
        Convert risk score to category and asset allocation
        
        Returns:
            Tuple of (risk_category, allocation_dict)
        """
        for (min_score, max_score), category in self.config.RISK_CATEGORIES.items():
            if min_score <= risk_score <= max_score:
                allocation = self.allocation_config.ALLOCATIONS[category]
                return category, allocation
        
        # Fallback to moderate if no category matches
        return "Moderate", self.allocation_config.ALLOCATIONS["Moderate"]
    
    def _validate_age(self, age: Union[int, float]) -> int:
        """Validate and normalize age input"""
        try:
            age = int(age)
            if age < 18 or age > 100:
                logger.warning(f"Age {age} outside normal range, using default 30")
                return 30
            return age
        except (ValueError, TypeError):
            logger.warning("Invalid age provided, using default 30")
            return 30
    
    def _validate_income(self, income: Union[int, float]) -> float:
        """Validate and normalize income input"""
        try:
            income = float(income)
            if income < 0:
                logger.warning("Negative income provided, using 0")
                return 0
            return income
        except (ValueError, TypeError):
            logger.warning("Invalid income provided, using default 50000")
            return 50000
    
    def _validate_risk_tolerance(self, risk_tolerance: Union[int, float]) -> int:
        """Validate risk tolerance score"""
        try:
            tolerance = int(risk_tolerance)
            if tolerance < 1 or tolerance > 10:
                logger.warning(f"Risk tolerance {tolerance} outside 1-10 range, using default 5")
                return 5
            return tolerance
        except (ValueError, TypeError):
            logger.warning("Invalid risk tolerance provided, using default 5")
            return 5
    
    def _get_default_conservative_profile(self) -> Dict:
        """Return default conservative profile in case of errors"""
        return {
            'risk_score': 0.3,
            'risk_category': 'Conservative',
            'debt_allocation': 70,
            'equity_allocation': 30,
            'factor_breakdown': {},
            'weighted_contributions': {},
            'error': 'Used default conservative profile due to calculation error'
        }
    
    def analyze_risk_sensitivity(self, base_profile: Dict, 
                                variations: Dict[str, list]) -> Dict:
        """
        Perform sensitivity analysis on risk factors
        
        Args:
            base_profile: Base user profile
            variations: Dict of parameter variations to test
        
        Returns:
            Dictionary with sensitivity analysis results
        """
        results = {}
        base_result = self.calculate_risk_score(base_profile)
        base_score = base_result['risk_score']
        
        for param, values in variations.items():
            param_results = []
            for value in values:
                test_profile = base_profile.copy()
                test_profile[param] = value
                
                result = self.calculate_risk_score(test_profile)
                param_results.append({
                    'value': value,
                    'risk_score': result['risk_score'],
                    'risk_category': result['risk_category'],
                    'score_change': result['risk_score'] - base_score
                })
            
            results[param] = param_results
        
        return {
            'base_score': base_score,
            'base_category': base_result['risk_category'],
            'sensitivity_results': results
        }


# Convenience functions for backward compatibility
def calculate_risk_score(age: int, income: float, current_savings: float, 
                        monthly_surplus: float, goals: Dict[int, float],
                        risk_tolerance: int = 5, weights: Optional[Dict] = None) -> float:
    """
    Legacy function for backward compatibility
    
    Returns only the risk score (float between 0-1)
    """
    engine = RiskAssessmentEngine()
    
    user_profile = {
        'age': age,
        'monthly_income': income,
        'current_savings': current_savings,
        'monthly_surplus': monthly_surplus,
        'goals': goals,
        'risk_tolerance_score': risk_tolerance
    }
    
    if weights:
        user_profile['custom_weights'] = weights
    
    result = engine.calculate_risk_score(user_profile)
    return result['risk_score']


def get_risk_category_from_score(risk_score: float) -> Tuple[str, Dict[str, float]]:
    """
    Legacy function for backward compatibility
    
    Returns risk category and allocation percentages
    """
    engine = RiskAssessmentEngine()
    category, allocation = engine._get_risk_category_and_allocation(risk_score)
    
    # Convert to percentage format for backward compatibility
    allocation_percent = {
        'debt': allocation['debt'],
        'equity': allocation['equity']
    }
    
    return category, allocation_percent


if __name__ == "__main__":
    # Example usage and testing
    print("🎯 Risk Assessment Engine - Testing")
    print("=" * 50)
    
    # Test profile 1: Young aggressive investor
    young_profile = {
        'age': 25,
        'monthly_income': 80000,
        'current_savings': 200000,
        'monthly_surplus': 25000,
        'goals': {60: 500000, 120: 1000000},  # 5 and 10 year goals
        'risk_tolerance_score': 8
    }
    
    # Test profile 2: Conservative older investor
    conservative_profile = {
        'age': 50,
        'monthly_income': 100000,
        'current_savings': 1000000,
        'monthly_surplus': 15000,
        'goals': {36: 200000},  # 3 year goal
        'risk_tolerance_score': 3
    }
    
    engine = RiskAssessmentEngine()
    
    print("\n📊 Young Aggressive Investor:")
    young_result = engine.calculate_risk_score(young_profile)
    print(f"Risk Score: {young_result['risk_score']}")
    print(f"Category: {young_result['risk_category']}")
    print(f"Allocation: {young_result['equity_allocation']}% Equity, {young_result['debt_allocation']}% Debt")
    
    print("\n📊 Conservative Older Investor:")
    conservative_result = engine.calculate_risk_score(conservative_profile)
    print(f"Risk Score: {conservative_result['risk_score']}")
    print(f"Category: {conservative_result['risk_category']}")
    print(f"Allocation: {conservative_result['equity_allocation']}% Equity, {conservative_result['debt_allocation']}% Debt")
    
    print("\n✅ Risk Assessment Engine test completed!")