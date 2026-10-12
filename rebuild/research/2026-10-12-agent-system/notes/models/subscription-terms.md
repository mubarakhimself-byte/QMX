# Vendor terms: consumer subscriptions via third-party tools/proxies
Fetched 2026-10-12. Facts with short quotes; not legal advice. UNVERIFIED = secondary source only.

## 1. Anthropic
### Claude Code legal-and-compliance (fetched 2026-10-12)
URL: https://code.claude.com/docs/en/legal-and-compliance
- Allowed: OAuth is "intended exclusively for purchasers of Claude Free, Pro, Max, Team, and Enterprise subscription plans" for ordinary use of Claude Code and other native Anthropic applications.
- Allowed: an end user may sign in to the unmodified Claude Code binary with their own subscription, including where a platform hosts it.
- Prohibited: Anthropic "does not permit third-party developers to offer Claude.ai login into their own applications".
- Prohibited: no routing requests "through Free, Pro, or Max plan credentials on behalf of their users".
- Prohibited: developers "may not collect, store, or intermediate Claude.ai credentials or session tokens".
- Developers building products (including Agent SDK) should use API key auth via Console or a cloud provider.
- Hosting Claude Code: binary must be unmodified; customers may not "pay for, resell, or intermediate Claude usage" for end users; each end user authenticates with their own credential.
- Enforcement: Anthropic may act "without prior notice".
- Plan limits assume "ordinary, individual usage of Claude Code and the Agent SDK".

### Agent SDK overview (fetched 2026-10-12)
URL: https://code.claude.com/docs/en/agent-sdk/overview
- Note: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits" in their products, including SDK agents. Use API key auth.
- SDK is governed by Commercial Terms of Service.

### Consumer Terms (effective Oct 8, 2025; fetched 2026-10-12)
URL: https://www.anthropic.com/legal/consumer-terms
- Sec 3: no access "through automated or non-human means", with an exception for access "via an Anthropic API Key".
- Sec 2: may not "make your Account available to anyone else"; may not share login info or API key.
- Sec 3: no reselling the Services; no bypassing protective measures.

### Usage-limit policy status (2026)
URL: https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan (fetched 2026-10-12; read through a summarizer)
- A June 15, 2026 change moving Agent SDK / `claude -p` / third-party app usage to a separate credit pool was paused; these uses "still draw from your subscription limits".
- Update dated Oct 7, 2026: Max and Team plans began including monthly API credits covering Agent SDK, `claude -p`, API, Managed Agents. Details UNVERIFIED.

### Enforcement reports (secondary, UNVERIFIED against Anthropic primary)
- Jan 9, 2026 OAuth blocks in third-party clients; Feb 19, 2026 docs clarification; Apr 4, 2026 subscription limits cut off for OpenClaw-type harnesses. Sources: https://winbuzzer.com/2026/02/19/anthropic-bans-claude-subscription-oauth-in-third-party-apps-xcxwbn/ and https://cybersecuritynews.com/claude-ends-openclaw-subscriptions/
- A claim that third-party access was reinstated behind "programmatic credit" on May 13-14, 2026 comes from one site (tech-insider.org); not confirmed. UNVERIFIED.

## 2. OpenAI
### Terms of Use (effective Jan 1, 2026; consumer; fetched 2026-10-12)
URL: https://openai.com/policies/row-terms-of-use/
- Prohibited: "may not share your account credentials or make your account available to anyone else".
- Prohibited: "Automatically or programmatically extract data or Output".
- Prohibited: circumvent "any rate limits or restrictions".
- Prohibited: use Output "to develop models that compete with OpenAI"; "Modify, copy, lease, sell or distribute any of our Services".
- Business Terms govern API and Enterprise (same URL).

### Codex auth (fetched 2026-10-12)
URL: https://learn.chatgpt.com/docs/auth
- Two sign-ins: ChatGPT (subscription) or API key (usage-based). For CI use API keys; enterprise access tokens are "intended for trusted scripts, schedulers, and private CI runners".
- "Treat ~/.codex/auth.json like a password." Page has no explicit third-party-app policy.

### Sign in with ChatGPT (SIWC), the sanctioned route
- Help article (fetched 2026-10-12): https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites
  - Allowed: plan usage in participating apps; "You don't need to create or share an OpenAI API key." Per-app weekly cap in Settings > Usage; credits only if opted in.
  - Commercial apps need Go/Plus/Pro user plan and OpenAI partnership (interest form); "Supported open-source tools remain available to all ChatGPT users."
- OSS docs overview (fetched 2026-10-12): https://developers.openai.com/siwc/token-sharing-open-source.md
  - For "open-source and locally hosted apps"; paid or remotely hosted apps must use the interest form.
  - Requires registering a user-defined agent with a stable `ext_agent_host_id` per host; each client_id bound to one user and workspace.
- Accounts: https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions.md : app must keep each account's credentials separate ("Never overwrite another account registration's credentials"); Plus 5-hour limit is shared across all apps.
- Limits: https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations.md : Responses API only, `store:false`, `stream:true`; many fields and hosted tools unsupported.
- Self-hosted VMs: https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms.md : credentials may be transferred to the user's own VM; host-specific attribution/revocation "not yet available".
- Not found: explicit pooling / account-rotation / general-purpose-proxy prohibition text on the pages fetched (ui-ux-guidelines, sign-in, errors pages NOT read). Design implies one user, own tool; pooling is not described as supported. Inference only, UNVERIFIED as a stated rule.

## 3. Google (brief)
- Gemini CLI ToS page (last commit Apr 10, 2026; fetched 2026-10-12): https://github.com/google-gemini/gemini-cli/blob/main/docs/resources/tos-privacy.md
  - Prohibited: directly accessing the services "using third-party software, tools, or services (for example, using OpenClaw with Gemini CLI OAuth) is a violation of applicable terms". May lead to suspension or termination.
  - Allowed: Google-account login in Gemini CLI, Gemini API key, Vertex AI key.
- Antigravity: secondary reports say Additional Terms clause 6 bars third-party software via Antigravity OAuth; Sept 2026 wording narrowed penalty to the Antigravity/Gemini CLI account. UNVERIFIED (not fetched from Google). Sources: https://moclaw.ai/blog/antigravity-account-suspended-third-party and https://discuss.ai.google.dev/t/urgent-mass-403-tos-bans-on-gemini-api-antigravity-for-open-source-cli-users-paid-tier/124508/7

## Takeaways for QMX (facts only)
- Anthropic: subscription OAuth only inside unmodified Claude Code/native apps; third-party apps must use API keys.
- OpenAI: the only documented path to use a ChatGPT plan inside another app is SIWC; local/open-source apps are explicitly supported.
- Google: third-party use of Gemini CLI/Antigravity OAuth is stated as a violation.
