from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf_report(
        name,
        income,
        credit_score,
        loan_amount,
        recommended_product,
        emi,
        risk,
        approval_probability,
        explanation):

    filename = "FinAssist_AI_Report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "FinAssist AI Loan Assessment Report",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            f"<b>Applicant:</b> {name}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Monthly Income:</b> ₹{income}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Credit Score:</b> {credit_score}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Loan Amount:</b> ₹{loan_amount}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Recommended Product:</b> {recommended_product}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Monthly EMI:</b> ₹{emi}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Risk Category:</b> {risk}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Approval Probability:</b> {approval_probability}%",
            styles["BodyText"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            "<b>AI Financial Advice</b>",
            styles["Heading2"]
        )
    )

    content.append(
        Paragraph(
            explanation,
            styles["BodyText"]
        )
    )

    doc.build(content)

    return filename