MARKET_ANALYSIS_TEMPLATE = """
Analyze the following market data for {sector}:
Data: {data}
Focus on: {key_metrics}
"""

def format_analysis_prompt(sector: str, data: str, key_metrics: str) -> str:
    return MARKET_ANALYSIS_TEMPLATE.format(
        sector=sector, 
        data=data, 
        key_metrics=key_metrics
    )