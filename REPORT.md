# Task 1 — Set Up the Agent Report

## Task 1A — Bare agent

### Checkpoint 1: "What is the agentic loop?"

**Session:** `cli:task1a-loop`

**Response:**
```
The agentic loop is the fundamental cycle that autonomous AI agents follow to accomplish tasks. It typically consists of these core stages:

1. Perceive — Gather information from the environment (user input, files, APIs, sensors, etc.)
2. Reason/Plan — Analyze the information, determine goals, and decide on actions
3. Act — Execute actions using available tools (write files, run commands, call APIs, send messages, etc.)
4. Observe — Receive feedback from the actions taken (outputs, errors, state changes)
5. Reflect/Iterate — Evaluate results, adjust the plan if needed, and continue the loop

 ┌─────────────┐
 │   Perceive  │
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │   Reason    │
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │    Act      │
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │   Observe   │
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │   Reflect   │───┐
 └─────────────┘   │
        └──────────┘
          (loop)

This loop continues until the task is complete or a stopping condition is met. The key difference between a simple chatbot and an agentic system is that agents can take autonomous actions in the world through tools, not just generate text responses.

In my case as nanobot, I go through this loop when you give me a task—I perceive your request, reason about what tools I need, act by calling them, observe the results, and reflect on whether I've completed your request or need to continue.
```

### Checkpoint 2: "What labs are available in our LMS?"

**Session:** `cli:task1a-labs`

**Response:**
The bare agent (without MCP) does not have access to real LMS data. Instead, it explored local filesystem directories looking for lab-related information. It searched through:
- `/root/se-toolkit-lab-8/nanobot/workspace`
- `/root/se-toolkit-lab-8`
- `/root/se-toolkit-lab-8/lab`
- `/root/se-toolkit-lab-8/lab/tasks/required`
- `/root/se-toolkit-lab-8/lab/tasks/optional`
- Read `README.md` and `index.md`

This demonstrates that without MCP tools, the agent can only access local files and cannot query the live LMS backend.

---

## Task 1B — Agent with LMS tools

### Checkpoint 1: "What labs are available?"

**Session:** `cli:task1b-labs`

**Response:**
```
Here are the available labs:

1. Lab 01 – Products, Architecture & Roles
2. Lab 02 — Run, Fix, and Deploy a Backend Service
3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
4. Lab 04 — Testing, Front-end, and AI Agents
5. Lab 05 — Data Pipeline and Analytics Dashboard
6. Lab 06 — Build Your Own Agent
7. Lab 07 — Build a Client with an AI Coding Agent
8. lab-08

Is there a specific lab you'd like to explore or get more information about?
```

The agent successfully called the `mcp_lms_lms_labs` tool and returned real lab names from the backend.

### Checkpoint 2: "Is the LMS backend healthy?"

**Session:** `cli:task1b-health`

**Response:**
```
Yes, the LMS backend is healthy. It's currently tracking 56 items.
```

The agent called `mcp_lms_lms_health` and reported the actual item count from the backend.

### Additional Test: "Which lab has the lowest pass rate?"

**Session:** `cli:task1b-pass-rates`

**Response:**
```
Based on the completion rates:

| Lab    | Completion Rate | Passed | Total |
|--------|-----------------|--------|-------|
| Lab 01 | 100.0%          | 258    | 258   |
| Lab 02 | 89.1%           | 131    | 147   |
| Lab 03 | 89.1%           | 156    | 175   |
| Lab 04 | 97.2%           | 239    | 246   |
| Lab 05 | 98.8%           | 247    | 250   |
| Lab 06 | 98.4%           | 242    | 246   |
| Lab 07 | 99.6%           | 238    | 239   |
| Lab 08 | 0.0%            | 0      | 0     |

Lab 08 has the lowest pass rate at 0.0%, but this appears to be because no students have attempted it yet (0 total submissions).

Among labs with actual submissions, Lab 02 and Lab 03 are tied for the lowest pass rate at 89.1%.
```

The agent successfully chained multiple tool calls:
1. First called `lms_labs` to get all lab IDs
2. Then called `lms_completion_rate` for each lab in parallel
3. Analyzed and compared the results
4. Provided a formatted table with insights

---

## Task 1C — Skill prompt

### Checkpoint: "Show me the scores" (without specifying a lab)

**Session:** `cli:task1c`

**Response:**
```
I'll help you see the scores! First, let me get the list of available labs so you can choose which one you'd like to see.

Here are the available labs:

1. Lab 01 – Products, Architecture & Roles
2. Lab 02 — Run, Fix, and Deploy a Backend Service
3. Lab 03 — Backend API: Explore, Debug, Implement, Deploy
4. Lab 04 — Testing, Front-end, and AI Agents
5. Lab 05 — Data Pipeline and Analytics Dashboard
6. Lab 06 — Build Your Own Agent
7. Lab 07 — Build a Client with an AI Coding Agent
8. lab-08

Which lab would you like to see the scores for? You can specify by number (1-8) or by the lab ID (e.g., "lab-04").
```

The skill prompt successfully taught the agent to:
1. Recognize that "scores" requires a lab parameter
2. Call `lms_labs` first when no lab is specified
3. Present labs with their titles as user-facing labels
4. Ask the user to choose a specific lab before proceeding

---

## Files Created/Modified

### nanobot/pyproject.toml
- Updated to use pinned nanobot version from archive commit `e7d371ec`
- Added `lms-mcp` as editable dependency from `../mcp`

### nanobot/config.json
- Configured MCP server `lms` with:
  - Command: `python -m mcp_lms`
  - Environment variables: `NANOBOT_LMS_BACKEND_URL` and `NANOBOT_LMS_API_KEY`

### nanobot/workspace/skills/lms/SKILL.md
- Created LMS skill prompt with:
  - Frontmatter (`name`, `description`, `always: true`)
  - Documentation of all 9 LMS MCP tools
  - Strategy rules for handling missing lab parameters
  - Formatting guidelines for percentages, counts, and tables
  - Error handling guidance

---

## Summary

| Part | Status | Key Result |
|------|--------|------------|
| 1A   | ✅     | Bare agent responds to general questions but has no LMS access |
| 1B   | ✅     | Agent with MCP returns real backend data (8 labs, 56 items) |
| 1C   | ✅     | Skill prompt teaches agent to ask for lab when not specified |
