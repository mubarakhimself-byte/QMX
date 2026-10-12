---
id: 06
title: Accounts and router
label: wayfinder:grilling
status: open
assignee:
blocked-by: [01, 05]
who-decides: Operator (HITL); his risk call on the Claude subscription path
---

## Question

How does QMX hold and route its resources? Cover:
- subscriptions vs API keys;
- more than one account per vendor;
- routing that knows each account's usage limits;
- one model per thread;
- the account-type badges;
- how the Claude subscription is used. Through the Claude Code worker only, or through a proxy too? That second part is the operator's risk call, made with `models-routing.md` §1 and the video notes in front of him.
