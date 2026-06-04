import os

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_explanation(
        name,
        income,
        credit_score,
        loan_amount,
        loan_type,
        emi):

    prompt = f"""
You are a professional financial advisor.

Customer Name: {name}
Monthly Income: ₹{income}
Credit Score: {credit_score}
Loan Amount: ₹{loan_amount}
Recommended Loan: {loan_type}
Estimated EMI: ₹{emi}

Explain:

1. Why the customer is eligible.
2. Why this loan was recommended.
3. Whether the EMI is manageable.
4. Give practical financial advice.

Keep the response under 150 words.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


def financial_chat(
        messages,
        name,
        income,
        credit_score,
        loan_amount,
        loan_type,
        emi):

    system_prompt = f"""
You are FinAssist AI.

You are a professional financial advisor.

Customer Profile:

Name: {name}
Monthly Income: ₹{income}
Credit Score: {credit_score}
Loan Amount: ₹{loan_amount}
Recommended Product: {loan_type}
Monthly EMI: ₹{emi}

Answer based on this profile.

Keep responses concise and practical.
"""

    chat_messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    chat_messages.extend(messages)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=chat_messages
    )

    return response.choices[0].message.content