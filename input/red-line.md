# Red Line

No agent may change a customer- or license-relevant state (production
data, shipped artifacts, contract scope) without a human explicitly
approving that specific change - regardless of how much trust has been
built up in the agent.

This holds as the default (opt-out only via a documented, explicit
R-CTRL approval) until the R-CTRL requirements phase defines and proves
a risk-based alternative through real pilot data.

A provider switch (primary model -> Bedrock fallback) must never
silently bypass the approval mechanism or change a tool contract. That
is part of this same line, not a separate concern.
