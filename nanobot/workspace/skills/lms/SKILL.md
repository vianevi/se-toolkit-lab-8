---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

You have access to the LMS (Learning Management System) backend via MCP tools. Use these tools to provide real-time data about labs, learners, and analytics.

## Available LMS Tools

- **lms_health** — Check if the LMS backend is healthy and get the item count
- **lms_labs** — List all labs available in the LMS
- **lms_learners** — List all learners registered in the LMS
- **lms_pass_rates** — Get pass rates (avg score and attempt count per task) for a specific lab
- **lms_timeline** — Get submission timeline (date + submission count) for a specific lab
- **lms_groups** — Get group performance (avg score + student count per group) for a specific lab
- **lms_top_learners** — Get top learners by average score for a specific lab
- **lms_completion_rate** — Get completion rate (passed / total) for a specific lab
- **lms_sync_pipeline** — Trigger the LMS sync pipeline to fetch latest data

## Strategy Rules

### When user asks about scores, pass rates, completion, groups, timeline, or top learners:

1. **If a lab is specified** — Call the appropriate tool directly with that lab identifier
2. **If no lab is specified** — First call `lms_labs` to get available labs, then ask the user to choose one

### Lab selection flow:

When the user needs to choose a lab:
1. Call `lms_labs` to fetch the current list
2. Present labs using their `title` field as the user-facing label
3. Use the lab's `id` field (e.g., "lab-01", "lab-02") as the value for tool calls
4. Let the shared structured-ui skill handle the choice presentation on supported channels

### Formatting results:

- **Percentages** — Display as "XX.X%" (e.g., "89.1%")
- **Counts** — Display as plain numbers with context (e.g., "258 students", "147 total")
- **Scores** — Display with one decimal place if applicable
- **Tables** — Use markdown tables for comparative data (multiple labs or groups)

### Response style:

- Keep responses concise and focused on the data
- Highlight key insights (e.g., "lowest", "highest", "tied")
- Note edge cases (e.g., "0% because no submissions yet")
- Offer follow-up help (e.g., "Would you like to see more details about a specific lab?")

### When user asks "what can you do?":

Explain your LMS capabilities clearly:
- I can check if the LMS backend is healthy
- I can list all available labs
- I can show pass rates, completion rates, and group performance for any lab
- I can show the submission timeline and top learners for any lab
- I can list all registered learners
- I need you to specify which lab for detailed analytics

### Error handling:

- If the backend is unhealthy, report the issue and suggest running the sync pipeline
- If a lab is not found, list available labs and ask the user to choose
- If data is empty, explain why (e.g., "no submissions yet")
