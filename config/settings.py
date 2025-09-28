class RiskAssessmentConfig:
    WEIGHTS = {
        'age_factor': 0.25,
        'income_factor': 0.20,
        'timeline_factor': 0.20,
        'surplus_factor': 0.15,
        'savings_factor': 0.10,
        'risk_tolerance_factor': 0.10
    }
    
    RISK_CATEGORIES = {
        (0.0, 0.2): 'Very Conservative',
        (0.2, 0.4): 'Conservative',
        (0.4, 0.6): 'Moderate',
        (0.6, 0.8): 'Growth',
        (0.8, 1.0): 'Aggressive'
    }
    
    INCOME_CAP = 100000

class AllocationConfig:
    ALLOCATIONS = {
        'Very Conservative': {'debt': 85, 'equity': 15},
        'Conservative': {'debt': 70, 'equity': 30},
        'Moderate': {'debt': 55, 'equity': 45},
        'Growth': {'debt': 35, 'equity': 65},
        'Aggressive': {'debt': 20, 'equity': 80}
    }