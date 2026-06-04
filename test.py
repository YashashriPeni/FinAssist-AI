from utils.eligibility import check_eligibility
from utils.emi import calculate_emi
from utils.recommendations import recommend_loan

eligible, message = check_eligibility(
    25,
    50000,
    750
)

print(eligible)
print(message)

recommended_loan, options = recommend_loan(
    750,
    50000,
    "Home"
)

print(recommended_loan)

emi = calculate_emi(
    500000,
    recommended_loan["interest_rate"],
    recommended_loan["tenure"]
)

print(emi)