from enum import Enum

class TransactionCategory(Enum):
    # Income Categories
    SALARY = "salary"
    FREELANCE = "freelance"
    INVESTMENT = "investment"
    BUSINESS = "business"
    BONUS = "bonus"
    OTHER_INCOME = "other_income"
    
    # Expense Categories
    FOOD_DINING = "food_dining"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    UTILITIES = "utilities"
    ENTERTAINMENT = "entertainment"
    SHOPPING_CLOTHING = "shopping_clothing"
    ELECTRONICS = "electronics"
    EDUCATION = "education"
    INSURANCE = "insurance"
    RENT_MORTGAGE = "rent_mortgage"
    GROCERIES = "groceries"
    TRAVEL = "travel"
    SUBSCRIPTIONS = "subscriptions"
    OTHER_EXPENSE = "other_expense"
    
    @classmethod
    def get_category_mapping(cls):
        """Mapping dari keyword Indonesia ke kategori standar"""
        return {
            # Food & Dining
            "makan": cls.FOOD_DINING,
            "makanan": cls.FOOD_DINING,
            "restoran": cls.FOOD_DINING,
            "cafe": cls.FOOD_DINING,
            "snack": cls.FOOD_DINING,
            "minuman": cls.FOOD_DINING,
            
            # Transportation
            "bensin": cls.TRANSPORTATION,
            "transportasi": cls.TRANSPORTATION,
            "ojek": cls.TRANSPORTATION,
            "taksi": cls.TRANSPORTATION,
            "bus": cls.TRANSPORTATION,
            "kereta": cls.TRANSPORTATION,
            "parkir": cls.TRANSPORTATION,
            
            # Electronics
            "laptop": cls.ELECTRONICS,
            "hp": cls.ELECTRONICS,
            "handphone": cls.ELECTRONICS,
            "komputer": cls.ELECTRONICS,
            "tv": cls.ELECTRONICS,
            "elektronik": cls.ELECTRONICS,
            
            # Clothing
            "baju": cls.SHOPPING_CLOTHING,
            "celana": cls.SHOPPING_CLOTHING,
            "sepatu": cls.SHOPPING_CLOTHING,
            "tas": cls.SHOPPING_CLOTHING,
            "pakaian": cls.SHOPPING_CLOTHING,
            
            # Income
            "gaji": cls.SALARY,
            "freelance": cls.FREELANCE,
            "bonus": cls.BONUS,
            "investasi": cls.INVESTMENT,
        }
    
    @classmethod
    def categorize(cls, text: str):
        """Mencari kategori berdasarkan text"""
        text_lower = text.lower()
        mapping = cls.get_category_mapping()
        
        for keyword, category in mapping.items():
            if keyword in text_lower:
                return category
        
        return cls.OTHER_EXPENSE  # Default fallback