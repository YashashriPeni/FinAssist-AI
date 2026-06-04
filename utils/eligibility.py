def check_eligibility(age, income, credit_score):

    if age < 18:
        return False, "Applicant must be at least 18 years old."

    if income < 25000:
        return False, "Monthly income is below the minimum requirement."

    if credit_score < 650:
        return False, "Credit score is too low."

    return True, "Eligible for loan consideration."