import plotly.graph_objects as go


def credit_score_gauge(score):

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Credit Score"},
            gauge={
                "axis": {"range": [300, 900]},
                "bar": {"thickness": 0.4},
                "steps": [
                    {"range": [300, 600], "color": "red"},
                    {"range": [600, 750], "color": "orange"},
                    {"range": [750, 900], "color": "green"}
                ]
            }
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    return fig


def approval_gauge(probability):

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability,
            title={"text": "Approval Probability (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"thickness": 0.4},
                "steps": [
                    {"range": [0, 40], "color": "red"},
                    {"range": [40, 70], "color": "orange"},
                    {"range": [70, 100], "color": "green"}
                ]
            }
        )
    )

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    return fig