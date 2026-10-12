# Cost Estimates and Agent Budgets

## Are these numbers what we actually pay?

No. Token Meter shows **estimates**, not invoices.

Token Meter reads the session logs that coding agents (Claude Code, Codex,
Cursor, and others) write on your machine. For each request it takes the
recorded token counts (input, output, cache writes, cache reads) and multiplies
them by the **public list price** for that model. It never connects to a billing
system, so it cannot see contract rates, enterprise discounts, committed-spend
agreements, gateway or Bedrock pricing, or seat-based subscriptions.

Read the cost as "what this local usage would cost at public rates."

## Why it differs from other tools

- **Scope.** Token Meter sees only local sessions on the machine it runs on.
  Admin consoles and gateway dashboards include every device, web and cloud
  sessions, CI, and other users.
- **Usage outside local coding sessions.** Claude.ai web and desktop chats, API
  calls from your own scripts or services, cloud and CI agents, and separate MCP
  or tool-provider charges do not appear in local session logs.
- **Cache pricing.** Coding sessions resend a lot of context, and most of it is
  billed as cache reads at a fraction of the input price. Tools that price all
  input at the full rate, or omit cache tokens, report very different totals.
- **Subagents.** Child-agent runs are included in the session total. Some tools
  omit them or show them separately.
- **Billing extras.** Web search ($10 per 1,000 searches), 1-hour cache writes,
  fast mode, and US-only data residency are priced when the local logs record
  them. A request that uses a model or pricing option Token Meter does not
  recognize is left out of the dollar total rather than guessed, so the total
  can read low.
- **Time windows.** Time zones, date cutoffs, and billing delays shift totals.

## What it is reliable for

Token counts come directly from local logs, and the pricing math is checked
against published rates. Use Token Meter to compare sessions, models, and
trends on your own machine: which workflows consume the most context, whether
caching is helping, and how spend changes over time. For actual spend, use the
provider's billing or admin console.

## Converting credits into agent budgets

Token Meter budgets are monthly US-dollar amounts set per agent (runtime). If
your allowance is issued as credits, convert each credit pool to dollars and add
them up for that agent:

```text
agent budget ($) = Σ (credits in pool × $ per credit)
```

### Example

| Agent | Credit pool | Credits | $ per credit | Dollars |
| --- | --- | ---: | ---: | ---: |
| Claude | Team allocation | 500 | $0.04 | $20.00 |
| Claude | Project top-up | 1,000 | $0.03 | $30.00 |
| **Claude budget** | | | | **$50.00** |
| Codex | Team allocation | 2,000 | $0.01 | $20.00 |
| **Codex budget** | | | | **$20.00** |

The monthly total is the sum of the agent budgets: $70.00.

### Set it in Token Meter

1. Open the dashboard and go to **Spend → Monthly budget**.
2. Choose **Set budgets** (or **Edit budgets** if one is already saved).
3. Enter each agent's dollar amount in its **Budget** field. Leave agents you
   do not use at `0`.
4. Optionally adjust the alert thresholds (80%, 90%, and 100% by default) and
   the default session budget.
5. Choose **Save budgets**. Budgets apply machine-wide and the menu bar uses
   them for alerts.

### Keep in mind

- Budgets are compared against Token Meter's **list-price estimate**. If your
  credit price reflects a negotiated rate, the estimate can use up the budget
  faster or slower than your real credit balance does.
- Budgets reset each calendar month. If credits cover a different period,
  divide by the number of months they cover.
- Spend outside local sessions does not count against these budgets. Check your
  provider's credit balance for the authoritative remaining amount.
