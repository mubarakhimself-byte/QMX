# Open decisions (what is still his; the design proceeds on the recommendation)

Answered on 2026-10-16 evening and folded in: E1 engine seat (yes), E2 tests (real models), E4 catch-up (yes), scheduling follows Hermes, nothing waits for him (ruling 57), design for the Library on his server (56), plain servers first with about 20 runs (55), the harness runs outside the sandbox (Rivet principle, adopted by the lead).

1. **What counts as an irreversible external effect.** These are the only steps that may wait for the inbox. Recommend: messages, posts, webhooks and outbound calls to non-QMX systems, plus app operations an app marks so; model spend, Library writes and file changes never count.
2. **Default self-improvement rule.** Recommend `self_improve: auto` for workflows he created or enabled, `propose_only` for templates he has not touched; `main` moves only by his click.
3. **PC agent nodes and the plan.** Recommend: in the default `runner_outside` mode a PC agent node may use a plan account (the chat stays on the host; only tool calls enter the box); the fallback `cli_inside` mode uses key providers only; the server never sees a plan token.
4. **Server specs before the first server packet.** Recommend a one-line check (`nproc; free -g; ls /dev/kvm; nvidia-smi`): under 32 GiB cap the semaphore at 10; E2B Embed only if `/dev/kvm` exists and pause/resume/fork is needed.
5. **`claude_workflow` node.** Needs harness request H4. Recommend off in v1; the engine's own fan-out across containers covers the need and is model-agnostic.
6. **Alert threshold for long pauses.** Recommend one inbox item after 6 hours of every allowed account being closed (UI-editable), nothing before.
