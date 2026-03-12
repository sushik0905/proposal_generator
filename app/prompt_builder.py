def build_prompt(data):
    return f"""
You are a senior consulting solution architect.

Write a professional project proposal using exactly these headings:

1. Executive Summary
2. Technical Approach
3. Timeline
4. Risk Assessment

Project Title: {data.project_title}
Industry: {data.industry}
Duration: {data.duration_months} months
Expected Users: {data.expected_users}
Tech Stack: {", ".join(data.tech_stack)}

Rules:
- Keep it concise and clear.
- Use only the 4 headings above.
- Write professional content under each heading.
"""