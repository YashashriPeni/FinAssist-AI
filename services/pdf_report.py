from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet


def sanitize_text_for_pdf(text):
    if not isinstance(text, str):
        text = str(text)
    # Replace Rupee symbol with standard ASCII representation
    text = text.replace("₹", "Rs. ")
    # Replace common HTML tags with clean equivalent or strip them
    text = text.replace("<b>", "").replace("</b>", "").replace("<strong>", "").replace("</strong>", "")
    text = text.replace("<p>", "").replace("</p>", "").replace("<br>", "").replace("<br/>", "")
    
    # Filter only standard printable ASCII characters to remove all emojis and non-supported unicode symbols
    clean_chars = []
    for char in text:
        val = ord(char)
        if 32 <= val <= 126:
            clean_chars.append(char)
            
    # Rebuild and remove markdown bold formatting
    clean_text = "".join(clean_chars).replace("**", "")
    return clean_text.strip()


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
            f"<b>Applicant:</b> {sanitize_text_for_pdf(name)}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Monthly Income:</b> Rs. {income}",
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
            f"<b>Loan Amount:</b> Rs. {loan_amount}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Recommended Product:</b> {sanitize_text_for_pdf(recommended_product)}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Monthly EMI:</b> Rs. {emi}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Risk Category:</b> {sanitize_text_for_pdf(risk)}",
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
            sanitize_text_for_pdf(explanation),
            styles["BodyText"]
        )
    )

    doc.build(content)

    return filename


def generate_health_pdf_report(
        name,
        income,
        emi,
        emi_ratio,
        credit_score,
        health_score,
        health_badge,
        suggestions):

    filename = "Financial_Health_Report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "FinAssist AI Financial Health Report",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(Paragraph(f"<b>Applicant:</b> {sanitize_text_for_pdf(name)}", styles["BodyText"]))
    content.append(Paragraph(f"<b>Monthly Income:</b> Rs. {income:,.2f}", styles["BodyText"]))
    content.append(Paragraph(f"<b>Monthly EMI:</b> Rs. {emi:,.2f}", styles["BodyText"]))
    content.append(Paragraph(f"<b>Debt-to-Income (DTI) Ratio:</b> {emi_ratio}%", styles["BodyText"]))
    content.append(Paragraph(f"<b>Credit Score:</b> {credit_score}", styles["BodyText"]))
    content.append(Paragraph(f"<b>Financial Health Score:</b> {health_score}/100 ({sanitize_text_for_pdf(health_badge)})", styles["BodyText"]))

    content.append(Spacer(1, 20))

    content.append(Paragraph("<b>Personalized Financial Advice</b>", styles["Heading2"]))
    content.append(Spacer(1, 10))

    for sug in suggestions:
        clean_sug = sanitize_text_for_pdf(sug)
        if clean_sug.startswith("- "):
            clean_sug = clean_sug[2:]
        elif clean_sug.startswith("-"):
            clean_sug = clean_sug[1:]
        content.append(Paragraph(f"&bull; {clean_sug}", styles["BodyText"]))
        content.append(Spacer(1, 6))

    doc.build(content)

    return filename