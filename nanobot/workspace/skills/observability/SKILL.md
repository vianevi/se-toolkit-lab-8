---
name: observability
description: Use observability MCP tools for logs and traces analysis
always: true
---

# Observability Skill

You have access to observability data via MCP tools for VictoriaLogs and VictoriaTraces. Use these tools to investigate errors, trace request flows, and diagnose issues.

## Available Observability Tools

- **obs_logs_search** — Search logs in VictoriaLogs using LogsQL query
- **obs_logs_error_count** — Count errors per service over a time window
- **obs_traces_list** — List recent traces for a service
- **obs_traces_get** — Fetch a specific trace by ID

## Strategy Rules

### When the user asks about errors or issues:

1. **Start with error count** — Call `obs_logs_error_count` to see if there are recent errors
   - Use a narrow time window (e.g., 10 minutes) for fresh data
   - Filter by service name if the user specifies one (e.g., "LMS backend")

2. **Search relevant logs** — If errors exist, call `obs_logs_search` to inspect them
   - Use query like `severity:ERROR service.name:"Learning Management Service" _time:10m`
   - Look for `trace_id` fields in error logs

3. **Fetch trace if available** — If you find a `trace_id`, call `obs_traces_get` to see the full request flow
   - This shows which services were involved and where the error occurred

4. **Summarize findings** — Provide a concise summary:
   - How many errors occurred
   - What the error was
   - Which service/component failed
   - The trace timeline if available

### When the user asks about traces:

1. **List recent traces** — Call `obs_traces_list` with the service name
2. **Fetch specific trace** — If user provides a trace ID, call `obs_traces_get`
3. **Explain the span hierarchy** — Show the request flow across services

### Query patterns:

**For LMS backend errors:**
```
severity:ERROR service.name:"Learning Management Service" _time:10m
```

**For all errors in a time window:**
```
severity:ERROR _time:60m
```

**For a specific event:**
```
event:db_query severity:ERROR _time:30m
```

### Response style:

- **Be concise** — Summarize findings, don't dump raw JSON
- **Highlight key info** — Error type, service, timestamp, trace ID
- **Show trace timeline** — If you fetched a trace, show the span hierarchy
- **Offer follow-up** — Ask if the user wants more details

### Example reasoning flow:

User: "Any LMS backend errors in the last 10 minutes?"

1. Call `obs_logs_error_count` with service="Learning Management Service", minutes=10
2. If count > 0, call `obs_logs_search` with query for LMS errors
3. Extract trace_id from error logs if present
4. Call `obs_traces_get` with the trace_id
5. Summarize: "Found X errors in the LMS backend. The error was [type] in [component]. Trace shows the request failed at [span]."

### When no errors found:

Report clearly: "No errors found in the LMS backend in the last 10 minutes."

### Important notes:

- Always use a scoped time window (e.g., 10 minutes) to avoid returning stale historical data
- Focus on the service the user asks about (e.g., LMS backend)
- If you see unrelated errors from other services, clarify that they're not from the requested service
