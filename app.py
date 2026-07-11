import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import importlib

# Dynamic hot-reloading to bypass Streamlit's process memory import cache
import services.database
importlib.reload(services.database)
import services.pdf_report
importlib.reload(services.pdf_report)
import utils.eligibility
importlib.reload(utils.eligibility)

from utils.eligibility import check_eligibility, calculate_approval_probability
from utils.emi import calculate_emi
from utils.recommendations import recommend_loan
from utils.charts import (
    credit_score_gauge,
    approval_gauge,
    financial_health_gauge
)

from services.ai_explainer import (
    generate_explanation,
    financial_chat
)

from services.database import (
    create_database,
    save_analysis,
    get_history,
    get_history_with_id,
    delete_history_item,
    clear_all_history
)

from services.pdf_report import generate_pdf_report, generate_health_pdf_report

st.set_page_config(
    page_title="FinAssist AI",
    page_icon="💰",
    layout="wide"
)

create_database()

# Session State Initializations
if "messages" not in st.session_state:
    st.session_state.messages = []
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "name" not in st.session_state:
    st.session_state.name = ""
if "age" not in st.session_state:
    st.session_state.age = 25
if "income" not in st.session_state:
    st.session_state.income = 50000.0
if "credit_score" not in st.session_state:
    st.session_state.credit_score = 750
if "loan_amount" not in st.session_state:
    st.session_state.loan_amount = 500000.0
if "purpose" not in st.session_state:
    st.session_state.purpose = "Home"
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None
if "confirm_delete_all" not in st.session_state:
    st.session_state.confirm_delete_all = False

# --------------------------------------------------------
# PAGE DEFINITIONS
# --------------------------------------------------------

def dashboard_page():
    st.subheader("📊 Loan Assessment Dashboard")
    
    if not st.session_state.analysis_done:
        st.warning("⚠️ Please perform the Loan Eligibility Assessment first to view your assessment dashboard.")
        return
        
    name = st.session_state.name
    income = st.session_state.income
    credit_score = st.session_state.credit_score
    loan_amount = st.session_state.loan_amount
    purpose = st.session_state.purpose
    
    eligible, message = check_eligibility(age=st.session_state.age, income=income, credit_score=credit_score)
    score = min(100, int((credit_score / 900) * 100))
    approval_probability = calculate_approval_probability(credit_score, income)
    
    if credit_score >= 800:
        risk = "🟢 Low Risk"
    elif credit_score >= 700:
        risk = "🟡 Medium Risk"
    else:
        risk = "🔴 High Risk"
        
    recommended_loan, _ = recommend_loan(credit_score, income, purpose)
    emi = calculate_emi(loan_amount, recommended_loan["interest_rate"], recommended_loan["tenure"])
    emi_ratio = round((emi / income) * 100, 2) if income > 0 else 0.0
    affordability = "🟢 Excellent" if emi_ratio < 20 else "🟡 Good" if emi_ratio < 35 else "🔴 Risky"

    # Save to history once
    if eligible:
        if "last_saved_key" not in st.session_state or st.session_state.last_saved_key != (name, income, credit_score, loan_amount):
            save_analysis(name, income, credit_score, loan_amount, recommended_loan["loan_type"], emi)
            st.session_state.last_saved_key = (name, income, credit_score, loan_amount)

    dash1, dash2, dash3 = st.columns(3)
    with dash1:
        st.metric("Eligibility Score", f"{score}%")
    with dash2:
        st.metric("Approval Probability", f"{approval_probability}%")
    with dash3:
        st.metric("Risk Category", risk)

    st.progress(score / 100)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Recommended Product", recommended_loan["loan_type"])
    with col2:
        st.metric("Interest Rate", f'{recommended_loan["interest_rate"]}%')
    with col3:
        st.metric("Monthly EMI", f'₹{emi:,.2f}')
    with col4:
        st.metric("EMI Burden", f"{emi_ratio}%")
    with col5:
        st.metric("Affordability", affordability)

    # FEATURE 1 - Financial Health Score Card
    st.markdown("---")
    st.subheader("🩺 Financial Health Score")

    cs_pts = (credit_score / 900.0) * 50.0
    if income >= 150000:
        income_pts = 20.0
    elif income >= 100000:
        income_pts = 17.0
    elif income >= 75000:
        income_pts = 14.0
    elif income >= 50000:
        income_pts = 10.0
    elif income >= 25000:
        income_pts = 7.0
    else:
        income_pts = 3.0

    if emi_ratio < 20:
        emi_pts = 20.0
    elif emi_ratio < 35:
        emi_pts = 15.0
    else:
        emi_pts = 5.0

    if credit_score >= 800:
        risk_pts = 10.0
    elif credit_score >= 700:
        risk_pts = 7.0
    else:
        risk_pts = 3.0

    health_score = min(100, max(0, int(cs_pts + income_pts + emi_pts + risk_pts)))
    health_badge = "🟢 Excellent" if health_score >= 85 else "🟡 Good" if health_score >= 70 else "🟠 Average" if health_score >= 50 else "🔴 Needs Improvement"

    health_col1, health_col2 = st.columns([1, 2])
    with health_col1:
        st.plotly_chart(financial_health_gauge(health_score), use_container_width=True)
    with health_col2:
        st.metric("Health Score Rating", f"{health_score}/100", delta=health_badge, delta_color="normal")
        st.markdown("### Personalized Improvement Suggestions")
        sug_list = []
        if emi_ratio >= 35:
            sug_list.append("- ⚠️ **Reduce EMI burden**: Your DTI ratio is high. Consider choosing a longer repayment tenure or reducing the loan principal.")
        elif emi_ratio >= 20:
            sug_list.append("- 💡 **Increase monthly savings**: Your monthly EMI takes up a notable portion of your income. Focus on budgeting to increase savings.")
        else:
            sug_list.append("- ✅ **Maintain low EMI burden**: Your debt servicing ratio is highly safe.")

        if credit_score < 750:
            sug_list.append("- ⚠️ **Improve credit score**: Focus on paying off credit card balances and maintaining a clean payment history.")
        else:
            sug_list.append("- ✅ **Maintain strong credit score**: Keep your utilization low and avoid excessive hard inquiries.")

        sug_list.append("- ℹ️ **Avoid multiple loan applications**: Limit hard credit checks within short timeframes.")
        sug_list.append("- ℹ️ **Maintain on-time repayments**: Pay credit lines early to keep building positive history.")

        for sug in sug_list:
            st.markdown(sug)

    st.markdown("---")
    st.subheader("📈 Financial Analytics")
    chart1, chart2 = st.columns(2)
    with chart1:
        st.plotly_chart(credit_score_gauge(credit_score), use_container_width=True)
    with chart2:
        st.plotly_chart(approval_gauge(approval_probability), use_container_width=True)


def eligibility_page():
    st.subheader("📝 Loan Eligibility Assessment")
    
    # Render input fields in body
    name = st.text_input("Full Name", value=st.session_state.name)
    age = st.number_input("Age", min_value=18, max_value=80, value=st.session_state.age)
    income = st.number_input("Monthly Income (₹)", min_value=0, value=int(st.session_state.income))
    credit_score = st.number_input("Credit Score", min_value=300, max_value=900, value=st.session_state.credit_score)
    loan_amount = st.number_input("Loan Amount (₹)", min_value=10000, value=int(st.session_state.loan_amount))
    
    purposes = ["Home", "Education", "Business", "Personal"]
    purpose_idx = purposes.index(st.session_state.purpose) if st.session_state.purpose in purposes else 0
    purpose = st.selectbox("Loan Purpose", purposes, index=purpose_idx)
    
    if st.button("Analyze Loan Eligibility"):
        st.session_state.name = name
        st.session_state.age = age
        st.session_state.income = income
        st.session_state.credit_score = credit_score
        st.session_state.loan_amount = loan_amount
        st.session_state.purpose = purpose
        st.session_state.analysis_done = True
        st.rerun()
        
    if st.session_state.analysis_done:
        # Precompute metrics
        eligible, message = check_eligibility(
            st.session_state.age,
            st.session_state.income,
            st.session_state.credit_score
        )
        
        if not eligible:
            st.error(message)
        else:
            st.success(message)
            
        # Checklist
        st.subheader("📋 Eligibility Checklist")
        
        age_ok = st.session_state.age >= 18
        age_icon = "✅" if age_ok else "❌"
        st.markdown(f"{age_icon} **Age requirement**: {'Passed' if age_ok else 'Failed'} (Applicant age: {st.session_state.age} years, minimum: 18)")
        
        inc_ok = st.session_state.income >= 25000
        inc_icon = "✅" if inc_ok else "❌"
        st.markdown(f"{inc_icon} **Income requirement**: {'Passed' if inc_ok else 'Failed'} (Monthly income: ₹{st.session_state.income:,.2f}, minimum: ₹25,000)")
        
        cs_ok = st.session_state.credit_score >= 650
        cs_icon = "✅" if cs_ok else "❌"
        st.markdown(f"{cs_icon} **Credit score evaluation**: {'Passed' if cs_ok else 'Failed'} (Credit score: {st.session_state.credit_score}, minimum: 650)")
        
        # Risk & DTI
        recommended_loan, _ = recommend_loan(st.session_state.credit_score, st.session_state.income, st.session_state.purpose)
        emi = calculate_emi(st.session_state.loan_amount, recommended_loan["interest_rate"], recommended_loan["tenure"])
        emi_ratio = round((emi / st.session_state.income) * 100, 2) if st.session_state.income > 0 else 0.0
        
        if st.session_state.credit_score >= 800:
            risk = "🟢 Low Risk"
            risk_ok = True
        elif st.session_state.credit_score >= 700:
            risk = "🟡 Medium Risk"
            risk_ok = True
        else:
            risk = "🔴 High Risk"
            risk_ok = False
            
        risk_icon = "✅" if risk_ok else "❌"
        st.markdown(f"{risk_icon} **Risk level evaluation**: assessed as **{risk}**.")
        
        emi_ok = emi_ratio < 35
        emi_icon = "✅" if emi_ok else "❌"
        aff = "🟢 Excellent" if emi_ratio < 20 else "🟡 Good" if emi_ratio < 35 else "🔴 Risky"
        st.markdown(f"{emi_icon} **EMI affordability explanation**: DTI ratio is **{emi_ratio}%** (Rating: {aff}).")
        
        st.markdown("### 📝 Recommendation Summary")
        if eligible:
            summary_text = (
                f"Based on the applicant's profile, they successfully passed all eligibility gating rules. "
                f"Given a good credit rating of **{st.session_state.credit_score}** and monthly cash flow of **₹{st.session_state.income:,.2f}**, they are matched with "
                f"the **{recommended_loan['loan_type']}** at an interest rate of **{recommended_loan['interest_rate']}%** for a tenure of **{recommended_loan['tenure']} years**. "
                f"The monthly EMI of **₹{emi:,.2f}** represents **{emi_ratio}%** of their income, which is classified as **{aff}** affordability, "
                f"minimizing default probabilities."
            )
        else:
            failures = []
            if not age_ok: failures.append("underage status")
            if not inc_ok: failures.append("insufficient monthly income")
            if not cs_ok: failures.append("low credit rating")
            if not emi_ok: failures.append("high debt servicing burden")
            summary_text = (
                f"The application has been flagged as ineligible due to: **{', '.join(failures)}**. "
                f"The recommended loan product **{recommended_loan['loan_type']}** is set to the basic tier with an interest rate of **{recommended_loan['interest_rate']}%** to reflect credit risk. "
                f"We advise addressing these checklist failures (e.g. optimizing credit lines or increasing income) before submitting a formal application."
            )
        st.info(summary_text)


def advisor_page():
    st.subheader("🤖 AI Financial Advisor")
    
    if not st.session_state.analysis_done:
        st.warning("⚠️ Please perform the Loan Eligibility Assessment first to access the AI Advisor.")
        return
        
    name = st.session_state.name
    income = st.session_state.income
    credit_score = st.session_state.credit_score
    loan_amount = st.session_state.loan_amount
    purpose = st.session_state.purpose
    
    recommended_loan, _ = recommend_loan(credit_score, income, purpose)
    emi = calculate_emi(loan_amount, recommended_loan["interest_rate"], recommended_loan["tenure"])
    
    if credit_score >= 800:
        risk = "🟢 Low Risk"
    elif credit_score >= 700:
        risk = "🟡 Medium Risk"
    else:
        risk = "🔴 High Risk"
    approval_probability = calculate_approval_probability(credit_score, income)

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


def health_report_page():
    st.subheader("🩺 Financial Health Report")
    
    if not st.session_state.analysis_done:
        st.warning("⚠️ Please perform the Loan Eligibility Assessment first to view your Financial Health Report.")
        return

    name = st.session_state.name
    income = st.session_state.income
    credit_score = st.session_state.credit_score
    loan_amount = st.session_state.loan_amount
    purpose = st.session_state.purpose
    
    recommended_loan, _ = recommend_loan(credit_score, income, purpose)
    emi = calculate_emi(loan_amount, recommended_loan["interest_rate"], recommended_loan["tenure"])
    emi_ratio = round((emi / income) * 100, 2) if income > 0 else 0.0
    approval_probability = calculate_approval_probability(credit_score, income)

    cs_pts = (credit_score / 900.0) * 30.0

    if income >= 150000:
        income_pts = 30.0
    elif income >= 100000:
        income_pts = 25.0
    elif income >= 75000:
        income_pts = 20.0
    elif income >= 50000:
        income_pts = 15.0
    elif income >= 25000:
        income_pts = 10.0
    else:
        income_pts = 5.0

    if emi_ratio < 20:
        emi_pts = 20.0
    elif emi_ratio < 35:
        emi_pts = 15.0
    else:
        emi_pts = 5.0

    app_pts = (approval_probability / 100.0) * 20.0

    health_score = min(100, max(0, int(cs_pts + income_pts + emi_pts + app_pts)))

    if health_score >= 85:
        health_badge = "🟢 Excellent"
    elif health_score >= 70:
        health_badge = "🟢 Good"
    elif health_score >= 50:
        health_badge = "🟡 Average"
    else:
        health_badge = "🔴 Needs Improvement"

    st.markdown(f"### Financial Health Score: **{health_score} / 100** ({health_badge})")
    st.progress(health_score / 100)

    st.markdown("---")

    # SECTION 2: Financial Snapshot
    st.markdown("### 📊 Financial Snapshot")
    snap_col1, snap_col2, snap_col3, snap_col4 = st.columns(4)
    with snap_col1:
        st.metric("Monthly Income", f"₹{income:,.2f}")
    with snap_col2:
        st.metric("Monthly EMI", f"₹{emi:,.2f}")
    with snap_col3:
        st.metric("Debt-to-Income (DTI) Ratio", f"{emi_ratio}%")
    with snap_col4:
        st.metric("Credit Score", str(credit_score))

    st.markdown("---")

    # SECTION 3 & 4: Plotly Doughnut & Breakdown
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### 🍩 Monthly Budget Allocation")
        emi_val = emi
        essential_val = income * 0.40
        savings_val = income * 0.20
        lifestyle_val = max(0.0, income - emi_val - essential_val - savings_val)

        vals = [essential_val, emi_val, savings_val, lifestyle_val]
        total_vals = sum(vals)
        if total_vals > 0:
            vals = [(v / total_vals) * income for v in vals]

        labels = ['Essential Expenses', 'EMI', 'Savings', 'Lifestyle Spending']
        fig_doughnut = go.Figure(data=[go.Pie(
            labels=labels,
            values=vals,
            hole=.4,
            textinfo='percent+label',
            marker=dict(colors=['#38BDF8', '#F59E0B', '#22C55E', '#818CF8'])
        )])
        fig_doughnut.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#FFFFFF"},
            height=260,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_doughnut, use_container_width=True)

    with col_right:
        st.markdown("### 💪 Financial Strength Breakdown")

        c_health = int((credit_score / 900.0) * 100)
        l_aff = int(max(0, min(100, 100 - emi_ratio)))
        s_cap = int(max(0, min(100, 100 - (emi_ratio * 1.5))))
        r_abil = int(approval_probability)

        badge_ch = "🟢" if c_health >= 80 else "🟡" if c_health >= 50 else "🔴"
        st.write(f"{badge_ch} **Credit Health**: {c_health}/100")
        st.progress(c_health / 100)

        badge_la = "🟢" if l_aff >= 80 else "🟡" if l_aff >= 50 else "🔴"
        st.write(f"{badge_la} **Loan Affordability**: {l_aff}/100")
        st.progress(l_aff / 100)

        badge_sc = "🟢" if s_cap >= 80 else "🟡" if s_cap >= 50 else "🔴"
        st.write(f"{badge_sc} **Savings Capacity**: {s_cap}/100")
        st.progress(s_cap / 100)

        badge_ra = "🟢" if r_abil >= 80 else "🟡" if r_abil >= 50 else "🔴"
        st.write(f"{badge_ra} **Repayment Ability**: {r_abil}/100")
        st.progress(r_abil / 100)

    st.markdown("---")

    # SECTION 5: Personalized Financial Advice
    st.markdown("### 💡 Personalized Financial Advice")

    sug_list = []
    if emi_ratio < 20:
        sug_list.append("- 🟢 **Your EMI is comfortably within safe limits.** Your Debt-to-Income (DTI) ratio is low and manageable.")
    elif emi_ratio < 35:
        sug_list.append("- 🟡 **Your EMI is moderate.** Try to avoid taking on additional debt for now.")
    else:
        sug_list.append("- 🔴 **Your EMI is high.** Focus on reducing your EMI burden by pre-paying high-interest debts.")

    if credit_score >= 750:
        sug_list.append("- 🟢 **Continue maintaining a credit score above 750.** This ensures eligibility for premium interest rates.")
    else:
        sug_list.append("- 🔴 **Improve your credit score.** Pay off outstanding card balances and maintain a flawless repayment history.")

    if emi_ratio >= 20:
        sug_list.append("- 💡 **Increase monthly savings by at least 10%.** Budget carefully to cut down on discretionary expenses.")
    else:
        sug_list.append("- 🟢 **Healthy savings potential.** Try to automate savings contributions each month.")

    sug_list.append("- ℹ️ **Avoid multiple loan applications in a short period.** Frequent inquiries will lower your credit rating.")
    sug_list.append("- ℹ️ **Build an emergency fund covering 6 months of expenses.** This protects your debt repayment capacity in case of income disruption.")

    with st.container(border=True):
        for sug in sug_list:
            st.markdown(sug)

    # SECTION 6: Download PDF Health Report
    st.markdown("### 📄 Export Report")
    health_pdf = generate_health_pdf_report(
        name,
        income,
        emi,
        emi_ratio,
        credit_score,
        health_score,
        health_badge,
        sug_list
    )
    with open(health_pdf, "rb") as f_pdf:
        st.download_button(
            label="📄 Download Financial Health Report",
            data=f_pdf,
            file_name="Financial_Health_Report.pdf",
            mime="application/pdf"
        )


def emi_calculator_page():
    st.subheader("🧮 EMI Calculator")
    st.write("Calculate monthly installments for various loan amounts, rates, and tenures.")
    
    default_amt = int(st.session_state.loan_amount) if st.session_state.analysis_done else 500000
    default_rate = 10.0
    default_tenure = 8
    
    if st.session_state.analysis_done:
        recommended_loan, _ = recommend_loan(st.session_state.credit_score, st.session_state.income, st.session_state.purpose)
        default_rate = float(recommended_loan["interest_rate"])
        default_tenure = int(recommended_loan["tenure"])

    calc_amt = st.number_input("Loan Amount (₹)", min_value=1000, value=default_amt, step=5000, key="calc_amt")
    calc_rate = st.number_input("Interest Rate (%)", min_value=1.0, max_value=30.0, value=default_rate, step=0.1, key="calc_rate")
    calc_tenure = st.number_input("Tenure (Years)", min_value=1, max_value=40, value=default_tenure, step=1, key="calc_tenure")
    
    calc_emi = calculate_emi(calc_amt, calc_rate, calc_tenure)
    st.metric("Calculated Monthly EMI", f"₹{calc_emi:,.2f}")
    
    total_payment = calc_emi * calc_tenure * 12
    total_interest = total_payment - calc_amt
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Interest Payable", f"₹{total_interest:,.2f}")
    with col2:
        st.metric("Total Repayment (Principal + Interest)", f"₹{total_payment:,.2f}")


def comparison_page():
    st.subheader("🏦 Loan Comparison Dashboard")
    
    if not st.session_state.analysis_done:
        st.warning("⚠️ Please perform the Loan Eligibility Assessment first to view the comparison dashboard.")
        return

    income = st.session_state.income
    credit_score = st.session_state.credit_score
    loan_amount = st.session_state.loan_amount
    purpose = st.session_state.purpose
    approval_probability = calculate_approval_probability(credit_score, income)
    
    recommended_loan, all_options = recommend_loan(credit_score, income, purpose)
    emi = calculate_emi(loan_amount, recommended_loan["interest_rate"], recommended_loan["tenure"])
    emi_ratio = round((emi / income) * 100, 2) if income > 0 else 0.0
    affordability = "🟢 Excellent" if emi_ratio < 20 else "🟡 Good" if emi_ratio < 35 else "🔴 Risky"

    computed_options = []
    for option in all_options:
        opt_emi = calculate_emi(loan_amount, option["interest_rate"], option["tenure"])
        opt_total_repayment = round(opt_emi * option["tenure"] * 12, 2)
        opt_total_interest = round(opt_total_repayment - loan_amount, 2)
        opt_fee_rate = 0.015 if "Basic" in option["loan_type"] else 0.010 if "Standard" in option["loan_type"] else 0.005
        opt_fee = round(loan_amount * opt_fee_rate, 2)

        is_rec = (option["loan_type"] == recommended_loan["loan_type"])

        if is_rec:
            badge = "⭐ Recommended"
        elif "Premium" in option["loan_type"]:
            badge = "🏆 Best Value"
        elif "Basic" in option["loan_type"]:
            badge = "⚡ Fastest Approval"
        else:
            badge = "💰 Lowest EMI"

        computed_options.append({
            "loan_type": option["loan_type"],
            "interest_rate": option["interest_rate"],
            "tenure": option["tenure"],
            "emi": opt_emi,
            "total_interest": opt_total_interest,
            "total_repayment": opt_total_repayment,
            "fee": opt_fee,
            "badge": badge,
            "is_recommended": is_rec
        })

    # SECTION 1: Loan Comparison Cards
    col_card1, col_card2, col_card3 = st.columns(3)

    for idx, opt in enumerate(computed_options):
        border_style = "border: 2px solid #22C55E; box-shadow: 0 4px 20px rgba(34, 197, 94, 0.2);" if opt["is_recommended"] else "border: 1px solid #334155;"
        bg_color = "#1E293B"
        card_html = f"""
        <div style="background-color: {bg_color}; {border_style} padding: 20px; border-radius: 12px; height: 100%; color: #FFFFFF; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #FFFFFF; font-size: 1.05rem; font-weight: 700;">{opt['loan_type']}</h4>
                <span style="background-color: #22C55E; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">{opt['badge']}</span>
            </div>
            <hr style="border-color: #334155; margin: 10px 0;">
            <div style="font-size: 0.9rem; line-height: 1.5; color: #D1D5DB;">
                <p style="margin: 4px 0;">Interest Rate: <strong style="color: #FFFFFF;">{opt['interest_rate']}%</strong></p>
                <p style="margin: 4px 0;">Loan Tenure: <strong style="color: #FFFFFF;">{opt['tenure']} Years</strong></p>
                <p style="margin: 4px 0;">Monthly EMI: <strong style="color: #22C55E; font-size: 1.05rem;">₹{opt['emi']:.2f}</strong></p>
                <p style="margin: 4px 0;">Total Interest: <strong style="color: #F59E0B;">₹{opt['total_interest']:.2f}</strong></p>
                <p style="margin: 4px 0;">Total Repayment: <strong style="color: #FFFFFF;">₹{opt['total_repayment']:.2f}</strong></p>
                <p style="margin: 4px 0;">Processing Fee: <strong style="color: #FFFFFF;">₹{opt['fee']:.2f}</strong></p>
            </div>
        </div>
        """
        with [col_card1, col_card2, col_card3][idx]:
            st.markdown(card_html, unsafe_allow_html=True)

    # SECTION 2: Comparison Charts
    st.markdown("### 📈 Visual Product Metrics")
    chart_row1_col1, chart_row1_col2 = st.columns(2)
    chart_row2_col1, chart_row2_col2 = st.columns(2)

    # Chart 1: Bar Chart - Monthly EMI
    fig_emi = go.Figure(data=[
        go.Bar(
            x=[opt["loan_type"] for opt in computed_options],
            y=[opt["emi"] for opt in computed_options],
            marker_color=["#38BDF8", "#818CF8", "#22C55E"],
            width=0.4
        )
    ])
    fig_emi.update_layout(
        title="Monthly EMI Comparison",
        yaxis=dict(title="EMI (₹)", gridcolor="#334155", tickfont=dict(color="#D1D5DB")),
        xaxis=dict(tickfont=dict(color="#D1D5DB")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FFFFFF"},
        height=280,
        margin=dict(l=40, r=40, t=50, b=40)
    )
    with chart_row1_col1:
        st.plotly_chart(fig_emi, use_container_width=True)

    # Chart 2: Bar Chart - Interest Rate
    fig_rate = go.Figure(data=[
        go.Bar(
            x=[opt["loan_type"] for opt in computed_options],
            y=[opt["interest_rate"] for opt in computed_options],
            marker_color=["#38BDF8", "#818CF8", "#22C55E"],
            width=0.4
        )
    ])
    fig_rate.update_layout(
        title="Interest Rate (APR) Comparison",
        yaxis=dict(title="Rate (%)", gridcolor="#334155", tickfont=dict(color="#D1D5DB")),
        xaxis=dict(tickfont=dict(color="#D1D5DB")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FFFFFF"},
        height=280,
        margin=dict(l=40, r=40, t=50, b=40)
    )
    with chart_row1_col2:
        st.plotly_chart(fig_rate, use_container_width=True)

    # Chart 3: Bar Chart - Total Repayment
    fig_repay = go.Figure(data=[
        go.Bar(
            x=[opt["loan_type"] for opt in computed_options],
            y=[opt["total_repayment"] for opt in computed_options],
            marker_color=["#38BDF8", "#818CF8", "#22C55E"],
            width=0.4
        )
    ])
    fig_repay.update_layout(
        title="Total Repayment Amount",
        yaxis=dict(title="Repayment (₹)", gridcolor="#334155", tickfont=dict(color="#D1D5DB")),
        xaxis=dict(tickfont=dict(color="#D1D5DB")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FFFFFF"},
        height=280,
        margin=dict(l=40, r=40, t=50, b=40)
    )
    with chart_row2_col1:
        st.plotly_chart(fig_repay, use_container_width=True)

    # Chart 4: Radar Chart
    fig_radar = go.Figure()
    for opt in computed_options:
        if "Premium" in opt["loan_type"]:
            scores = [9.0, 9.0, 9.5, 4.0, 9.0]
        elif "Standard" in opt["loan_type"]:
            scores = [7.5, 7.0, 7.5, 6.0, 7.0]
        else:
            scores = [5.0, 4.0, 5.0, 9.0, 4.0]
        
        fig_radar.add_trace(go.Scatterpolar(
            r=scores + [scores[0]],
            theta=['Affordability', 'Risk Checked', 'Interest Savings', 'Repayment Cost', 'Flexibility', 'Affordability'],
            fill='toself',
            name=opt["loan_type"]
        ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#334155", tickfont=dict(color="#D1D5DB")),
            angularaxis=dict(gridcolor="#334155", tickfont=dict(color="#D1D5DB"))
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#FFFFFF"},
        height=280,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(font=dict(color="#FFFFFF"))
    )
    with chart_row2_col2:
        st.plotly_chart(fig_radar, use_container_width=True)

    # SECTION 3: Savings Analysis
    sorted_repayments = sorted(computed_options, key=lambda x: x["total_repayment"])
    cheapest_loan = sorted_repayments[0]
    expensive_loan = sorted_repayments[-1]
    
    rec_opt = [o for o in computed_options if o["is_recommended"]][0]
    money_saved_total = max(0.0, expensive_loan["total_repayment"] - rec_opt["total_repayment"])
    
    max_emi_opt = sorted(computed_options, key=lambda x: x["emi"])[-1]
    emi_diff = max(0.0, max_emi_opt["emi"] - rec_opt["emi"])
    repayment_diff = max(0.0, expensive_loan["total_repayment"] - cheapest_loan["total_repayment"])

    st.markdown(
        f"""
        <div style="background-color: #1E293B; border: 1px solid #334155; padding: 20px; border-radius: 12px; margin-top: 20px; color: #FFFFFF;">
            <h4 style="margin: 0 0 10px 0; color: #FFFFFF; font-size: 1.1rem; font-weight: 700;">💰 Financial Savings Analysis</h4>
            <hr style="border-color: #334155; margin: 10px 0;">
            <div style="font-size: 0.95rem; line-height: 1.6; color: #D1D5DB;">
                <p style="margin: 5px 0;">Cheapest Loan product (by Lifetime Cost): <strong>{cheapest_loan['loan_type']} (₹{cheapest_loan['total_repayment']:.2f})</strong></p>
                <p style="margin: 5px 0;">Most Expensive Loan product (by Lifetime Cost): <strong>{expensive_loan['loan_type']} (₹{expensive_loan['total_repayment']:.2f})</strong></p>
                <p style="margin: 5px 0;">Money saved by choosing the recommended option: <strong style="color: #22C55E;">₹{money_saved_total:,.2f}</strong></p>
                <p style="margin: 5px 0;">Difference in monthly EMI (Savings vs max EMI product): <strong style="color: #22C55E;">₹{emi_diff:,.2f}</strong></p>
                <p style="margin: 5px 0;">Lifetime repayment savings gap (Min vs Max product cost): <strong style="color: #22C55E;">₹{repayment_diff:,.2f}</strong></p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # SECTION 4: Recommendation Summary
    st.markdown("### 📝 Recommendation Summary")
    summary_text = (
        f"The **{recommended_loan['loan_type']}** is recommended because it offers the best balance "
        f"between monthly EMI (₹{rec_opt['emi']:.2f}), lifetime repayment amount (₹{rec_opt['total_repayment']:.2f}), "
        f"and overall affordability while keeping financial risk {affordability.lower()} and APR at a competitive {rec_opt['interest_rate']}%."
    )
    st.info(summary_text)
    
    st.markdown("---")
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
                st.session_state.name,
                f"₹{st.session_state.income}",
                f"₹{st.session_state.loan_amount}",
                recommended_loan["loan_type"],
                f"₹{emi}",
                f"{emi_ratio}%",
                "Low Risk" if credit_score >= 700 else "High Risk",
                f"{approval_probability}%"
            ]
        }
    )
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )


def history_page():
    st.subheader("🗄 Previous Loan Analyses")

    # Confirmation State Initializations
    if "confirm_delete_id" not in st.session_state:
        st.session_state.confirm_delete_id = None
    if "confirm_delete_all" not in st.session_state:
        st.session_state.confirm_delete_all = False

    history_with_ids = get_history_with_id()

    if not history_with_ids:
        st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 1.1rem; padding: 25px;'>No previous loan analyses available.</p>", unsafe_allow_html=True)
    else:
        # Delete All button at the top
        if st.button("🚨 Delete All History", key="del_all_btn"):
            st.session_state.confirm_delete_all = True

        if st.session_state.confirm_delete_all:
            st.warning("⚠️ Are you sure you want to permanently clear ALL analyses from history?")
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                if st.button("Yes, Confirm Delete All", key="confirm_del_all_yes"):
                    clear_all_history()
                    st.success("Successfully cleared all history from SQLite database!")
                    st.session_state.confirm_delete_all = False
                    st.rerun()
            with col_c2:
                if st.button("No, Cancel", key="confirm_del_all_no"):
                    st.session_state.confirm_delete_all = False
                    st.rerun()

        to_delete_id = st.session_state.confirm_delete_id
        if to_delete_id is not None:
            st.warning(f"⚠️ Are you sure you want to permanently delete Record #{to_delete_id}?")
            col_ic1, col_ic2 = st.columns(2)
            with col_ic1:
                if st.button("Yes, Confirm Delete", key="confirm_del_yes"):
                    delete_history_item(to_delete_id)
                    st.success(f"Successfully deleted Record #{to_delete_id}!")
                    st.session_state.confirm_delete_id = None
                    st.rerun()
            with col_ic2:
                if st.button("No, Cancel", key="confirm_del_no"):
                    st.session_state.confirm_delete_id = None
                    st.rerun()

        # Render Table Headers
        hdr_col1, hdr_col2, hdr_col3, hdr_col4, hdr_col5, hdr_col6, hdr_col7 = st.columns([1.5, 1.2, 1, 1.2, 2, 1, 0.8])
        with hdr_col1: st.write("**Applicant**")
        with hdr_col2: st.write("**Income**")
        with hdr_col3: st.write("**Credit Score**")
        with hdr_col4: st.write("**Loan Amount**")
        with hdr_col5: st.write("**Recommended Product**")
        with hdr_col6: st.write("**EMI**")
        with hdr_col7: st.write("**Action**")

        st.markdown("---")

        # Render Rows inside scrollable container
        with st.container(height=380):
            for index, row in enumerate(history_with_ids):
                r_id, r_app, r_inc, r_cs, r_amt, r_prod, r_emi = row
                
                bg_color = "#334155" if index % 2 == 0 else "#1E293B"
                
                row_col1, row_col2, row_col3, row_col4, row_col5, row_col6, row_col7 = st.columns([1.5, 1.2, 1, 1.2, 2, 1, 0.8])
                with row_col1: st.markdown(f"<div style='background-color: {bg_color}; padding: 8px; border-radius: 4px; color: #FFFFFF; font-weight: 600;'>{r_app}</div>", unsafe_allow_html=True)
                with row_col2: st.markdown(f"<div style='background-color: {bg_color}; padding: 8px; border-radius: 4px; color: #F1F5F9; font-weight: 500;'>₹{r_inc:,.2f}</div>", unsafe_allow_html=True)
                with row_col3: st.markdown(f"<div style='background-color: {bg_color}; padding: 8px; border-radius: 4px; color: #F1F5F9; font-weight: 500;'>{r_cs}</div>", unsafe_allow_html=True)
                with row_col4: st.markdown(f"<div style='background-color: {bg_color}; padding: 8px; border-radius: 4px; color: #F1F5F9; font-weight: 500;'>₹{r_amt:,.2f}</div>", unsafe_allow_html=True)
                with row_col5: st.markdown(f"<div style='background-color: {bg_color}; padding: 8px; border-radius: 4px; color: #F1F5F9; font-weight: 500;'>{r_prod}</div>", unsafe_allow_html=True)
                with row_col6: st.markdown(f"<div style='background-color: {bg_color}; padding: 8px; border-radius: 4px; color: #FFFFFF; font-weight: 700;'>₹{r_emi:,.2f}</div>", unsafe_allow_html=True)
                with row_col7:
                    if st.button("🗑️", key=f"del_row_{r_id}"):
                        st.session_state.confirm_delete_id = r_id
                        st.rerun()

        st.metric(
            "Total Analyses Stored",
            len(history_with_ids)
        )


# --------------------------------------------------------
# NAVIGATION SYSTEM SETUP
# --------------------------------------------------------

pg_dash = st.Page(dashboard_page, title="Dashboard", icon="🏠", default=True)
pg_elig = st.Page(eligibility_page, title="Loan Eligibility", icon="📝")
pg_advisor = st.Page(advisor_page, title="AI Financial Advisor", icon="🤖")
pg_health = st.Page(health_report_page, title="Financial Health Report", icon="📊")
pg_emi = st.Page(emi_calculator_page, title="EMI Calculator", icon="💰")
pg_comp = st.Page(comparison_page, title="Loan Comparison", icon="⚖")
pg_hist = st.Page(history_page, title="Loan History", icon="🗂")

pg = st.navigation([
    pg_dash,
    pg_elig,
    pg_advisor,
    pg_health,
    pg_emi,
    pg_comp,
    pg_hist
], position="hidden")

# Renders dynamic Applicant Snapshot below built-in navigation links in the sidebar
with st.sidebar:
    st.subheader("🏦 FinAssist AI")
    st.markdown("---")
    
    st.page_link(pg_dash, label="Dashboard", icon="🏠")
    st.page_link(pg_elig, label="Loan Eligibility", icon="📝")
    st.page_link(pg_advisor, label="AI Financial Advisor", icon="🤖")
    st.page_link(pg_health, label="Financial Health Report", icon="📊")
    st.page_link(pg_emi, label="EMI Calculator", icon="💰")
    st.page_link(pg_comp, label="Loan Comparison", icon="⚖")
    st.page_link(pg_hist, label="Loan History", icon="🗂")
    
    st.markdown("---")
    st.markdown("### 📋 Applicant Snapshot")
    if st.session_state.analysis_done:
        st.write(f"👤 **Name**: {st.session_state.name}")
        st.write(f"💳 **Credit Score**: {st.session_state.credit_score}")
        st.write(f"💰 **Income**: ₹{st.session_state.income:,.2f}")
        st.write(f"🏠 **Loan Purpose**: {st.session_state.purpose}")
    else:
        st.info("No applicant selected.")

# Execute Page Run
pg.run()
