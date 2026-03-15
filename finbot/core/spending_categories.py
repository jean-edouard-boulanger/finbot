"""Plaid Personal Finance Category (PFC) taxonomy.

Each entry is (primary_category, detailed_category, description).
"""

PLAID_PFC_TAXONOMY: list[tuple[str, str, str]] = [
    ("INCOME", "INCOME_DIVIDENDS", "Dividends from investments"),
    ("INCOME", "INCOME_INTEREST_EARNED", "Interest earned on accounts"),
    ("INCOME", "INCOME_RETIREMENT_PENSION", "Pension or retirement income"),
    ("INCOME", "INCOME_TAX_REFUND", "Tax refund"),
    ("INCOME", "INCOME_UNEMPLOYMENT", "Unemployment income"),
    ("INCOME", "INCOME_WAGES", "Wages and salary"),
    ("INCOME", "INCOME_OTHER_INCOME", "Other income"),
    ("TRANSFER_IN", "TRANSFER_IN_CASH_ADVANCES_AND_LOANS", "Cash advances and loans"),
    ("TRANSFER_IN", "TRANSFER_IN_DEPOSIT", "Deposits"),
    ("TRANSFER_IN", "TRANSFER_IN_INVESTMENT_AND_RETIREMENT_FUNDS", "Investment and retirement funds received"),
    ("TRANSFER_IN", "TRANSFER_IN_SAVINGS", "Savings transfers in"),
    ("TRANSFER_IN", "TRANSFER_IN_ACCOUNT_TRANSFER", "Account transfers in"),
    ("TRANSFER_IN", "TRANSFER_IN_OTHER_TRANSFER_IN", "Other transfers in"),
    ("TRANSFER_OUT", "TRANSFER_OUT_INVESTMENT_AND_RETIREMENT_FUNDS", "Investment and retirement funds sent"),
    ("TRANSFER_OUT", "TRANSFER_OUT_SAVINGS", "Savings transfers out"),
    ("TRANSFER_OUT", "TRANSFER_OUT_WITHDRAWAL", "Withdrawals"),
    ("TRANSFER_OUT", "TRANSFER_OUT_ACCOUNT_TRANSFER", "Account transfers out"),
    ("TRANSFER_OUT", "TRANSFER_OUT_OTHER_TRANSFER_OUT", "Other transfers out"),
    ("LOAN_PAYMENTS", "LOAN_PAYMENTS_CAR_PAYMENT", "Car payment"),
    ("LOAN_PAYMENTS", "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT", "Credit card payment"),
    ("LOAN_PAYMENTS", "LOAN_PAYMENTS_PERSONAL_LOAN_PAYMENT", "Personal loan payment"),
    ("LOAN_PAYMENTS", "LOAN_PAYMENTS_MORTGAGE_PAYMENT", "Mortgage payment"),
    ("LOAN_PAYMENTS", "LOAN_PAYMENTS_STUDENT_LOAN_PAYMENT", "Student loan payment"),
    ("LOAN_PAYMENTS", "LOAN_PAYMENTS_OTHER_PAYMENT", "Other loan payments"),
    ("BANK_FEES", "BANK_FEES_ATM_FEES", "ATM fees"),
    ("BANK_FEES", "BANK_FEES_FOREIGN_TRANSACTION_FEES", "Foreign transaction fees"),
    ("BANK_FEES", "BANK_FEES_INSUFFICIENT_FUNDS", "Insufficient funds fees"),
    ("BANK_FEES", "BANK_FEES_INTEREST_CHARGE", "Interest charges"),
    ("BANK_FEES", "BANK_FEES_OVERDRAFT_FEES", "Overdraft fees"),
    ("BANK_FEES", "BANK_FEES_OTHER_BANK_FEES", "Other bank fees"),
    ("ENTERTAINMENT", "ENTERTAINMENT_CASINOS_AND_GAMBLING", "Casinos and gambling"),
    ("ENTERTAINMENT", "ENTERTAINMENT_MUSIC_AND_AUDIO", "Music and audio"),
    ("ENTERTAINMENT", "ENTERTAINMENT_SPORTING_EVENTS_AMUSEMENT_PARKS_AND_MUSEUMS", "Events, amusement parks, museums"),
    ("ENTERTAINMENT", "ENTERTAINMENT_TV_AND_MOVIES", "TV and movies"),
    ("ENTERTAINMENT", "ENTERTAINMENT_VIDEO_GAMES", "Video games"),
    ("ENTERTAINMENT", "ENTERTAINMENT_OTHER_ENTERTAINMENT", "Other entertainment"),
    ("FOOD_AND_DRINK", "FOOD_AND_DRINK_BEER_WINE_AND_LIQUOR", "Beer, wine, and liquor"),
    ("FOOD_AND_DRINK", "FOOD_AND_DRINK_COFFEE", "Coffee shops"),
    ("FOOD_AND_DRINK", "FOOD_AND_DRINK_FAST_FOOD", "Fast food"),
    ("FOOD_AND_DRINK", "FOOD_AND_DRINK_GROCERIES", "Groceries"),
    ("FOOD_AND_DRINK", "FOOD_AND_DRINK_RESTAURANT", "Restaurants"),
    ("FOOD_AND_DRINK", "FOOD_AND_DRINK_OTHER_FOOD_AND_DRINK", "Other food and drink"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_BOOKSTORES_AND_NEWSSTANDS", "Bookstores and newsstands"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_CLOTHING_AND_ACCESSORIES", "Clothing and accessories"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_CONVENIENCE_STORES", "Convenience stores"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_DEPARTMENT_STORES", "Department stores"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_DISCOUNT_STORES", "Discount stores"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_ELECTRONICS", "Electronics"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_GIFTS_AND_NOVELTIES", "Gifts and novelties"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_OFFICE_SUPPLIES", "Office supplies"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_ONLINE_MARKETPLACES", "Online marketplaces"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_PET_SUPPLIES", "Pet supplies"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_SPORTING_GOODS", "Sporting goods"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_SUPERSTORES", "Superstores"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_TOBACCO_AND_VAPE", "Tobacco and vape"),
    ("GENERAL_MERCHANDISE", "GENERAL_MERCHANDISE_OTHER_GENERAL_MERCHANDISE", "Other general merchandise"),
    ("HOME_IMPROVEMENT", "HOME_IMPROVEMENT_FURNITURE", "Furniture"),
    ("HOME_IMPROVEMENT", "HOME_IMPROVEMENT_HARDWARE", "Hardware"),
    ("HOME_IMPROVEMENT", "HOME_IMPROVEMENT_REPAIR_AND_MAINTENANCE", "Repair and maintenance"),
    ("HOME_IMPROVEMENT", "HOME_IMPROVEMENT_SECURITY", "Security"),
    ("HOME_IMPROVEMENT", "HOME_IMPROVEMENT_OTHER_HOME_IMPROVEMENT", "Other home improvement"),
    ("MEDICAL", "MEDICAL_DENTAL_CARE", "Dental care"),
    ("MEDICAL", "MEDICAL_EYE_CARE", "Eye care"),
    ("MEDICAL", "MEDICAL_NURSING_CARE", "Nursing care"),
    ("MEDICAL", "MEDICAL_PHARMACIES_AND_SUPPLEMENTS", "Pharmacies and supplements"),
    ("MEDICAL", "MEDICAL_PRIMARY_CARE", "Primary care"),
    ("MEDICAL", "MEDICAL_VETERINARY_SERVICES", "Veterinary services"),
    ("MEDICAL", "MEDICAL_OTHER_MEDICAL", "Other medical"),
    ("PERSONAL_CARE", "PERSONAL_CARE_GYMS_AND_FITNESS_CENTERS", "Gyms and fitness centers"),
    ("PERSONAL_CARE", "PERSONAL_CARE_HAIR_AND_BEAUTY", "Hair and beauty"),
    ("PERSONAL_CARE", "PERSONAL_CARE_LAUNDRY_AND_DRY_CLEANING", "Laundry and dry cleaning"),
    ("PERSONAL_CARE", "PERSONAL_CARE_OTHER_PERSONAL_CARE", "Other personal care"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_ACCOUNTING_AND_FINANCIAL_PLANNING", "Accounting and financial planning"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_AUTOMOTIVE", "Automotive services"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_CHILDCARE", "Childcare"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_CONSULTING_AND_LEGAL", "Consulting and legal"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_EDUCATION", "Education"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_INSURANCE", "Insurance"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_POSTAGE_AND_SHIPPING", "Postage and shipping"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_STORAGE", "Storage"),
    ("GENERAL_SERVICES", "GENERAL_SERVICES_OTHER_GENERAL_SERVICES", "Other general services"),
    ("GOVERNMENT_AND_NON_PROFIT", "GOVERNMENT_AND_NON_PROFIT_DONATIONS", "Donations"),
    (
        "GOVERNMENT_AND_NON_PROFIT",
        "GOVERNMENT_AND_NON_PROFIT_GOVERNMENT_DEPARTMENTS_AND_AGENCIES",
        "Government departments",
    ),
    ("GOVERNMENT_AND_NON_PROFIT", "GOVERNMENT_AND_NON_PROFIT_TAX_PAYMENT", "Tax payments"),
    ("GOVERNMENT_AND_NON_PROFIT", "GOVERNMENT_AND_NON_PROFIT_OTHER_GOVERNMENT_AND_NON_PROFIT", "Other government"),
    ("TRANSPORTATION", "TRANSPORTATION_BIKES_AND_SCOOTERS", "Bikes and scooters"),
    ("TRANSPORTATION", "TRANSPORTATION_GAS", "Gas"),
    ("TRANSPORTATION", "TRANSPORTATION_PARKING", "Parking"),
    ("TRANSPORTATION", "TRANSPORTATION_PUBLIC_TRANSIT", "Public transit"),
    ("TRANSPORTATION", "TRANSPORTATION_TAXIS_AND_RIDE_SHARES", "Taxis and ride shares"),
    ("TRANSPORTATION", "TRANSPORTATION_TOLLS", "Tolls"),
    ("TRANSPORTATION", "TRANSPORTATION_OTHER_TRANSPORTATION", "Other transportation"),
    ("TRAVEL", "TRAVEL_FLIGHTS", "Flights"),
    ("TRAVEL", "TRAVEL_LODGING", "Lodging"),
    ("TRAVEL", "TRAVEL_RENTAL_CARS", "Rental cars"),
    ("TRAVEL", "TRAVEL_OTHER_TRAVEL", "Other travel"),
    ("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_GAS_AND_ELECTRICITY", "Gas and electricity"),
    ("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_INTERNET_AND_CABLE", "Internet and cable"),
    ("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_RENT", "Rent"),
    ("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_SEWAGE_AND_WASTE_MANAGEMENT", "Sewage and waste management"),
    ("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_TELEPHONE", "Telephone"),
    ("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_WATER", "Water"),
    ("RENT_AND_UTILITIES", "RENT_AND_UTILITIES_OTHER_UTILITIES", "Other utilities"),
]

PRIMARY_CATEGORIES: list[str] = sorted(set(entry[0] for entry in PLAID_PFC_TAXONOMY))


def format_category_label(category: str) -> str:
    """Convert a category code like 'FOOD_AND_DRINK' to 'Food & Drink'."""
    return category.replace("_AND_", " & ").replace("NON_PROFIT", "Non-Profit").replace("_", " ").title()


PRIMARY_CATEGORY_LABELS: dict[str, str] = {cat: format_category_label(cat) for cat in PRIMARY_CATEGORIES}


def get_taxonomy_prompt_text() -> str:
    """Return a formatted taxonomy reference suitable for LLM prompts."""
    lines = ["Primary Category | Detailed Category | Description"]
    lines.append("-" * 80)
    for primary, detailed, description in PLAID_PFC_TAXONOMY:
        lines.append(f"{primary} | {detailed} | {description}")
    return "\n".join(lines)
