
import streamlit as st
import pandas as pd

from utils.eligibility import check_eligibility
from utils.emi import calculate_emi
from utils.recommendations import recommend_loan
from utils.charts import (
    credit_score_gauge,
    approval_gauge
)


from services.ai_explainer import (
    generate_explanation,
    financial_chat
)

from services.database import (
    create_database,
    save_analysis,
    get_history
)

from services.pdf_report import generate_pdf_report

st.set_page_config(
    page_title="FinAssist AI",
    page_icon="💰",
    layout="wide"
)

create_database()

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:

    st.title("FinAssist AI")

    st.write(
        "AI-Powered Loan Recommendation Agent"
    )

    st.info(
        "Analyzes income, credit score, and loan requirements."
    )

st.title("💰 FinAssist AI")

st.subheader(
    "Intelligent Loan Advisory Agent"
)

st.write(
    """
    FinAssist AI analyzes your financial profile,
    evaluates eligibility,
    calculates EMI,
    recommends suitable loans,
    and provides AI-powered financial guidance.
    """
)

name = st.text_input("Full Name")

age = st.number_input(
    "Age",
    min_value=18,
    max_value=80,
    value=25
)

income = st.number_input(
    "Monthly Income (₹)",
    min_value=0,
    value=50000
)

credit_score = st.number_input(
    "Credit Score",
    min_value=300,
    max_value=900,
    value=750
)

loan_amount = st.number_input(
    "Loan Amount (₹)",
    min_value=10000,
    value=500000
)

purpose = st.selectbox(
    "Loan Purpose",
    [
        "Home",
        "Education",
        "Business",
        "Personal"
    ]
)

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if st.button("Analyze Loan Eligibility"):
    st.session_state.analysis_done = True

if st.session_state.analysis_done:

    eligible, message = check_eligibility(
        age,
        income,
        credit_score
    )

    if not eligible:

        st.error(message)

    else:

        st.success(message)

        score = min(
            100,
            int((credit_score / 900) * 100)
        )

        approval_probability = min(
            95,
            int(
                (credit_score * 0.6 / 9)
                +
                min(income / 2000, 40)
            )
        )

        if credit_score >= 800:
            risk = "🟢 Low Risk"

        elif credit_score >= 700:
            risk = "🟡 Medium Risk"

        else:
            risk = "🔴 High Risk"

        recommended_loan, all_options = recommend_loan(
            credit_score,
            income,
            purpose
        )

        emi = calculate_emi(
            loan_amount,
            recommended_loan["interest_rate"],
            recommended_loan["tenure"]
        )

        save_analysis(
            name,
            income,
            credit_score,
            loan_amount,
            recommended_loan["loan_type"],
            emi
        )

        emi_ratio = round(
            (emi / income) * 100,
            2
        )

        if emi_ratio < 20:
            affordability = "🟢 Excellent"

        elif emi_ratio < 35:
            affordability = "🟡 Good"

        else:
            affordability = "🔴 Risky"

        st.subheader("📊 Loan Assessment Dashboard")

        dash1, dash2, dash3 = st.columns(3)

        with dash1:
            st.metric(
                "Eligibility Score",
                f"{score}%"
            )

        with dash2:
            st.metric(
                "Approval Probability",
                f"{approval_probability}%"
            )

        with dash3:
            st.metric(
                "Risk Category",
                risk
            )

        st.progress(score / 100)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Recommended Product",
                recommended_loan["loan_type"]
            )

        with col2:
            st.metric(
                "Interest Rate",
                f'{recommended_loan["interest_rate"]}%'
            )

        with col3:
            st.metric(
                "Monthly EMI",
                f'₹{emi}'
            )

        with col4:
            st.metric(
                "EMI Burden",
                f"{emi_ratio}%"
            )

        with col5:
            st.metric(
                "Affordability",
                affordability
            )

        st.subheader("📈 Financial Analytics")

        chart1, chart2 = st.columns(2)

        with chart1:
            st.plotly_chart(
                credit_score_gauge(
                    credit_score
                ),
                use_container_width=True
            )

        with chart2:
            st.plotly_chart(
                approval_gauge(
                    approval_probability
                ),
                use_container_width=True
            )

        st.subheader("🏦 Loan Comparison Engine")

        comparison_data = []

        for option in all_options:

            option_emi = calculate_emi(
                loan_amount,
                option["interest_rate"],
                option["tenure"]
            )

            comparison_data.append({
                "Product": option["loan_type"],
                "Interest Rate": f'{option["interest_rate"]}%',
                "Tenure (Years)": option["tenure"],
                "Monthly EMI": f'₹{option_emi}'
            })

        st.dataframe(
            pd.DataFrame(comparison_data),
            use_container_width=True
        )

        st.subheader("📊 Financial Summary")

        summary_df = pd.DataFrame(
            {
                "Field": [
                    "Applicant",
                    "Monthly Income",
                    "Loan Amount",
                    "Recommended Product",
                    "Monthly EMI",
                    "EMI Burden",
                    "Risk Category",
                    "Approval Probability"
                ],
                "Value": [
                    name,
                    f"₹{income}",
                    f"₹{loan_amount}",
                    recommended_loan["loan_type"],
                    f"₹{emi}",
                    f"{emi_ratio}%",
                    risk,
                    f"{approval_probability}%"
                ]
            }
        )

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("🗄 Previous Loan Analyses")

        history = get_history()

        if history:

            history_df = pd.DataFrame(
                history,
                columns=[
                    "Applicant",
                    "Income",
                    "Credit Score",
                    "Loan Amount",
                    "Recommended Product",
                    "EMI"
                ]
            )

            st.dataframe(
                history_df,
                use_container_width=True
            )

            st.metric(
                "Total Analyses Stored",
                len(history_df)
            )

        st.subheader("🤖 AI Financial Advisor")

        explanation = generate_explanation(
            name,
            income,
            credit_score,
            loan_amount,
            recommended_loan["loan_type"],
            emi
        )

        st.write(explanation)

        pdf_file = generate_pdf_report(
            name,
            income,
            credit_score,
            loan_amount,
            recommended_loan["loan_type"],
            emi,
            risk,
            approval_probability,
            explanation
        )

        with open(pdf_file, "rb") as pdf:

            st.download_button(
                label="📄 Download PDF Report",
                data=pdf,
                file_name="FinAssist_AI_Report.pdf",
                mime="application/pdf"
            )

        st.subheader("💬 Ask FinAssist AI")



        for message in st.session_state.messages:

            with st.chat_message(message["role"]):
                st.write(message["content"])

        user_question = st.chat_input(
            "Ask anything about loans, EMI, credit score, or financial planning..."
        )

        if user_question:

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": user_question
                }
            )

            with st.chat_message("user"):
                st.write(user_question)

            answer = financial_chat(
                user_question,
                name,
                income,
                credit_score,
                loan_amount,
                recommended_loan["loan_type"],
                emi
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer
                }
            )

            with st.chat_message("assistant"):
                st.write(answer)

st.markdown("---")

st.caption(
    "Powered by Groq Llama 3.3 70B | FinAssist AI v1.3"
)

