def recommend_loan(
        credit_score,
        income,
        purpose):

    if purpose == "Home":
        loan_name = "Home Loan"

    elif purpose == "Education":
        loan_name = "Education Loan"

    elif purpose == "Business":
        loan_name = "Business Expansion Loan"

    else:
        loan_name = "Personal Loan"

    options = [
        {
            "loan_type": f"{loan_name} (Basic)",
            "interest_rate": 12.5,
            "tenure": 5
        },
        {
            "loan_type": f"{loan_name} (Standard)",
            "interest_rate": 10.0,
            "tenure": 8
        },
        {
            "loan_type": f"{loan_name} (Premium)",
            "interest_rate": 8.5,
            "tenure": 10
        }
    ]

    score = 0

    # Credit Score Weight (70 points)

    if credit_score >= 800:
        score += 70

    elif credit_score >= 750:
        score += 60

    elif credit_score >= 700:
        score += 50

    elif credit_score >= 650:
        score += 35

    else:
        score += 20

    # Income Weight (30 points)

    if income >= 150000:
        score += 30

    elif income >= 100000:
        score += 25

    elif income >= 75000:
        score += 20

    elif income >= 50000:
        score += 15

    else:
        score += 10

    # Final Recommendation

    if score >= 90:
        recommended = options[2]     # Premium

    elif score >= 70:
        recommended = options[1]     # Standard

    else:
        recommended = options[0]     # Basic

    return recommended, options