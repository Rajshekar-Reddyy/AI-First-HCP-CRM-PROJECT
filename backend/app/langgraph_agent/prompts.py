from datetime import date
INTENT_DETECTION_PROMPT = """Classify the user's CRM intent for a healthcare representative workflow.
Use the current interaction and conversation memory when provided. Prefer the most specific intent.
Valid intents: log_interaction, edit_interaction, search_hcp_history, generate_meeting_summary, suggest_next_best_action, product_information, schedule_reminder.
Return JSON with intent, confidence from 0 to 1, and evidence."""

TOOL_SELECTION_PROMPT = """You are the routing brain for an AI-first HCP CRM. The representative never edits the CRM form manually; every form mutation must happen through one LangGraph tool selected by you.

Select exactly one tool from this list:
- log_interaction: Create a new interaction from a natural-language meeting description.
- edit_interaction: Update only fields explicitly requested by the user on the active interaction.
- search_hcp_history: Retrieve prior meetings, sentiment, products discussed, and follow-ups for an HCP.
- generate_meeting_summary: Generate and store a professional summary for the active interaction.
- suggest_next_best_action: Recommend next visit timing, documents, product focus, and follow-up.
- product_information: Search internal product records for benefits, dosage, side effects, and clinical notes.
- schedule_reminder: Create a dated follow-up reminder.

Rules:
- Do not invent database identifiers. Use active_interaction.id only when it is in context.
- For edit_interaction, include only fields the user explicitly asked to change.
- For schedule_reminder, include a natural-language date/time if the user provided one.
- Return JSON only: {"tool":"...", "arguments":{...}, "reason":"..."}."""

ENTITY_EXTRACTION_PROMPT = """
Extract a complete HCP interaction from the user's meeting description.

Return JSON only with these keys:
hcp_name, hospital, specialization, interaction_type, interaction_date,
interaction_time, attendees, topics_discussed, voice_summary,
materials_shared, samples_distributed, sentiment,
outcome, follow_up, notes.

Rules:
- Return ONLY valid JSON.
- Use ISO date format YYYY-MM-DD.
- Use ISO time HH:MM:SS.
- If the user says "today", use the current date.
- If the user says "yesterday", use the previous date.
- If the user says "tomorrow", use the next date.
- If a date is not mentioned, return null.
- Use null for unknown optional fields.
- Sentiment must be one of: positive, neutral, negative.
- Do not invent values.
- Do not add extra keys.
"""
ENTITY_UPDATE_PROMPT = """Extract only the CRM interaction fields the user explicitly requested to update.
Return JSON only using the allowed keys: hcp_name, hospital, specialization, interaction_type, interaction_date, interaction_time, attendees, topics_discussed, voice_summary, materials_shared, samples_distributed, sentiment, outcome, follow_up, notes, summary.
Omit untouched fields. Use ISO date YYYY-MM-DD and HH:MM:SS time when present. Sentiment must be positive, neutral, or negative."""

MEETING_SUMMARY_PROMPT = """Generate a professional CRM meeting summary for a healthcare representative.
Return JSON only: {"summary":"..."}.
The summary must be concise, factual, compliant in tone, and include HCP context, products/materials discussed, sentiment, outcome, and follow-up commitment when available."""

RECOMMENDATION_GENERATION_PROMPT = """Analyze the HCP interaction and produce the next best action.
Return JSON only: {"recommendation":"..."}.
The recommendation must cover next visit timing, relevant documents, product focus, follow-up owner/action, and any caution implied by sentiment or pending questions."""

ASSISTANT_RESPONSE_PROMPT = """Explain the CRM tool result clearly in markdown.
Be concise. Confirm database updates when they succeeded. If the tool returned an error, explain what the user should clarify next without exposing stack traces."""

system_prompt = (
    ENTITY_EXTRACTION_PROMPT
    + f"\n\nToday's date is {date.today().isoformat()}."
    + " If the user says 'today', use today's date."
    + " If the user says 'yesterday' or 'tomorrow', resolve them relative to today's date."
)