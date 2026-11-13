# Spike 2026-11-14 00:03:23

PASS 1 parent pid 8992 exited=True; child pid 2560 alive after it=True (detached); child finished its run=True
PASS 2 inside the worktree written=True; outside written=False; denials ['Write']; kind nocontract; text 'Only `inside.txt` was written. The write to `outside.txt` was refused by a ship hook that allows writes only in the worktree or evidence folder. I did not try another tool to get around it.'
PASS 3 ended on its own after 16s (kind ok); denials ['WebFetch']; text 'DONE refused'
PASS 4 asked 'haiku'; modelUsage names ['claude-haiku-5-5']
PASS 5 kind ok; session_id d25bef10-6b23-426c-afa2-b5fdaea1efa6 vs passed d25bef10-6b23-426c-afa2-b5fdaea1efa6
PASS 6 ran in C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real\workers\spike\fresh-child-41884696; it said 'C:\\Users\\Mubarak\\AppData\\Local\\Temp\\claude\\704f33895ba593ad\\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\\scratchpad\\spike-real\\workers\\spike\\fresh-child-41884696'; ended on its own with kind ok
PASS 7 loggedIn True, authMethod claude.ai, apiProvider firstParty, plan max; worker env holds only ['CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH']

## Raw

Run 1 (probes 1, 4, 5, 6) is `spike-child`, started by `ship spike --parent` as a detached child; its log: `C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real\workers\spike\child.log`.

### spike-child

cwd: `C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real\workers\spike\fresh-child-41884696`

```
claude -p "Use no tools. Reply with exactly one line: the word DONE, a space, then your current working directory exactly as your environment states it." --model haiku --effort low --settings D:\QMX-worktrees\ship-kit\tools\ship\roles\builder.json --permission-mode dontAsk --permission-prompts none --disallowedTools Agent --add-dir C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real --add-dir D:\factory --session-id d25bef10-6b23-426c-afa2-b5fdaea1efa6 --name "spike: spike-real child" --output-format json
```

stdout:

```json
{"duration_api_ms":2965,"stop_reason":"end_turn","session_id":"d25bef10-6b23-426c-afa2-b5fdaea1efa6","total_cost_usd":0.0093582,"usage":{"input_tokens":2,"cache_creation_input_tokens":46115,"cache_read_input_tokens":0,"output_tokens":270,"output_tokens_details":{"thinking_tokens":172},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":46115,"ephemeral_5m_input_tokens":0},"inference_geo":"global","iterations":[{"input_tokens":2,"output_tokens":270,"cache_read_input_tokens":0,"cache_creation_input_tokens":46115,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":46115},"type":"message"}],"speed":"standard","fallback_credit":null},"modelUsage":{"claude-haiku-5-5":{"inputTokens":2,"outputTokens":270,"cacheReadInputTokens":0,"cacheCreationInputTokens":46115,"webSearchRequests":0,"costUSD":0.0093582,"contextWindow":1000000,"maxOutputTokens":128000,"thinkingTokens":172,"cacheCreationEphemeral5mInputTokens":0,"cacheCreationEphemeral1hInputTokens":46115,"canonicalModel":"claude-haiku-5-5","provider":"firstParty","costBasis":"list"}},"permission_denials":[],"terminal_reason":"completed","fast_mode_state":"off","fast_mode_disabled_reason":"sdk_opt_in_required","subagent_stats":{"spawned":0,"requested":{"background":0,"foreground":0,"unset":0},"started_in_background":0,"max_depth":0,"spawned_by_subagents":0,"completed":0,"failed":0,"killed":{"parent":0,"user":0,"system":0},"refused":{"depth_limit":0,"concurrency_limit":0,"budget":0},"by_type":{}},"safety_stops":0,"is_error":false,"num_turns":1,"subtype":"success","api_error_status":null,"result":"DONE C:\\Users\\Mubarak\\AppData\\Local\\Temp\\claude\\704f33895ba593ad\\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\\scratchpad\\spike-real\\workers\\spike\\fresh-child-41884696","ttft_ms":3083,"type":"result","duration_ms":4826,"uuid":"49485dc8-640e-400b-becc-162c9a30cc1b","ttft_stream_ms":2254,"time_to_request_ms":646,"first_content_frame_ms":2255,"queued_turn_count":0,"result_index":0,"credential_expires_at":"2026-12-12T03:35:57.587Z"}
```

stderr:

```
(empty)
```

### spike-hook

cwd: `C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real\wt\slice-sp1`

```
claude -p "Use the Write tool twice and no other tool: write the text x to C:/Users/Mubarak/AppData/Local/Temp/claude/704f33895ba593ad/dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26/scratchpad/spike-real/wt/slice-sp1/inside.txt, then write the text x to C:/Users/Mubarak/AppData/Local/Temp/claude/704f33895ba593ad/dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26/scratchpad/spike-real/outside.txt. Then reply with exactly one line: DONE written" --model haiku --effort low --settings D:\QMX-worktrees\ship-kit\tools\ship\roles\builder.json --permission-mode dontAsk --permission-prompts none --disallowedTools Agent --add-dir C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real --add-dir D:\factory --session-id e945e1a8-3562-406f-878d-c9765fd66059 --name "spike: spike-real hook" --output-format json
```

stdout:

```json
{"duration_api_ms":5503,"stop_reason":"end_turn","session_id":"e945e1a8-3562-406f-878d-c9765fd66059","total_cost_usd":0.006116820000000001,"usage":{"input_tokens":4,"cache_creation_input_tokens":25624,"cache_read_input_tokens":71212,"output_tokens":559,"output_tokens_details":{"thinking_tokens":186},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":25624,"ephemeral_5m_input_tokens":0},"inference_geo":"global","iterations":[{"input_tokens":2,"output_tokens":181,"cache_read_input_tokens":46281,"cache_creation_input_tokens":4274,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":4274},"type":"message"}],"speed":"standard","fallback_credit":null},"modelUsage":{"claude-haiku-5-5":{"inputTokens":4,"outputTokens":559,"cacheReadInputTokens":71212,"cacheCreationInputTokens":25624,"webSearchRequests":0,"costUSD":0.006116820000000001,"contextWindow":1000000,"maxOutputTokens":128000,"thinkingTokens":186,"cacheCreationEphemeral5mInputTokens":0,"cacheCreationEphemeral1hInputTokens":25624,"canonicalModel":"claude-haiku-5-5","provider":"firstParty","costBasis":"list"}},"permission_denials":[{"tool_name":"Write","tool_use_id":"toolu_01Xn81tixa6gHyH58FNoHrbU","tool_input":{"file_path":"C:\\Users\\Mubarak\\AppData\\Local\\Temp\\claude\\704f33895ba593ad\\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\\scratchpad\\spike-real\\outside.txt","content":"x"}}],"terminal_reason":"completed","fast_mode_state":"off","fast_mode_disabled_reason":"sdk_opt_in_required","subagent_stats":{"spawned":0,"requested":{"background":0,"foreground":0,"unset":0},"started_in_background":0,"max_depth":0,"spawned_by_subagents":0,"completed":0,"failed":0,"killed":{"parent":0,"user":0,"system":0},"refused":{"depth_limit":0,"concurrency_limit":0,"budget":0},"by_type":{}},"safety_stops":0,"is_error":false,"num_turns":3,"subtype":"success","api_error_status":null,"result":"Only `inside.txt` was written. The write to `outside.txt` was refused by a ship hook that allows writes only in the worktree or evidence folder. I did not try another tool to get around it.","ttft_ms":2502,"type":"result","duration_ms":8446,"uuid":"ebf6467d-5808-4dd4-9e20-6729d47b992f","ttft_stream_ms":2105,"time_to_request_ms":600,"first_content_frame_ms":2106,"queued_turn_count":0,"result_index":0,"credential_expires_at":"2026-12-12T03:35:57.587Z"}
```

stderr:

```
(empty)
```

### spike-perm

cwd: `C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real\workers\spike\fresh-perm-add4b64a`

```
claude -p "Use the WebFetch tool once to fetch https://example.com. If it is refused, do not retry and use no other tool; reply with exactly one line: DONE refused" --model haiku --effort low --settings D:\QMX-worktrees\ship-kit\tools\ship\roles\builder.json --permission-mode dontAsk --permission-prompts none --disallowedTools Agent --add-dir C:\Users\Mubarak\AppData\Local\Temp\claude\704f33895ba593ad\dd8f4ab2-2445-405b-b3e4-38c7d7aa1b26\scratchpad\spike-real --add-dir D:\factory --session-id 3a067e81-64aa-4424-9af6-80dcaeb91b08 --name "spike: spike-real perm" --output-format json
```

stdout:

```json
{"duration_api_ms":6561,"stop_reason":"end_turn","session_id":"3a067e81-64aa-4424-9af6-80dcaeb91b08","total_cost_usd":0.006533990000000001,"usage":{"input_tokens":6,"cache_creation_input_tokens":25753,"cache_read_input_tokens":121279,"output_tokens":340,"output_tokens_details":{"thinking_tokens":162},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":25753,"ephemeral_5m_input_tokens":0},"inference_geo":"global","iterations":[{"input_tokens":2,"output_tokens":48,"cache_read_input_tokens":50216,"cache_creation_input_tokens":468,"cache_creation":{"ephemeral_5m_input_tokens":0,"ephemeral_1h_input_tokens":468},"type":"message"}],"speed":"standard","fallback_credit":null},"modelUsage":{"claude-haiku-5-5":{"inputTokens":6,"outputTokens":340,"cacheReadInputTokens":121279,"cacheCreationInputTokens":25753,"webSearchRequests":0,"costUSD":0.006533990000000001,"contextWindow":1000000,"maxOutputTokens":128000,"thinkingTokens":162,"cacheCreationEphemeral5mInputTokens":0,"cacheCreationEphemeral1hInputTokens":25753,"canonicalModel":"claude-haiku-5-5","provider":"firstParty","costBasis":"list"}},"permission_denials":[{"tool_name":"WebFetch","tool_use_id":"toolu_01Hta5AZZxYuvQWRQhbNSVxp","tool_input":{"url":"https://example.com","prompt":"Summarize the main content of this page in one sentence."}}],"terminal_reason":"completed","fast_mode_state":"off","fast_mode_disabled_reason":"sdk_opt_in_required","subagent_stats":{"spawned":0,"requested":{"background":0,"foreground":0,"unset":0},"started_in_background":0,"max_depth":0,"spawned_by_subagents":0,"completed":0,"failed":0,"killed":{"parent":0,"user":0,"system":0},"refused":{"depth_limit":0,"concurrency_limit":0,"budget":0},"by_type":{}},"safety_stops":0,"is_error":false,"num_turns":3,"subtype":"success","api_error_status":null,"result":"DONE refused","ttft_ms":3321,"type":"result","duration_ms":9684,"uuid":"98e389e6-11c1-4ef8-9f5d-04823b1ddefb","ttft_stream_ms":3143,"time_to_request_ms":601,"first_content_frame_ms":3144,"queued_turn_count":0,"result_index":0,"credential_expires_at":"2026-12-12T03:35:57.587Z"}
```

stderr:

```
(empty)
```

### auth

```
claude auth status
```

```json
{
  "loggedIn": true,
  "authMethod": "claude.ai",
  "apiProvider": "firstParty",
  "analyticsDisabled": false,
  "projectsDirectory": "C:\\Users\\Mubarak\\.claude\\projects",
  "configDirectory": "C:\\Users\\Mubarak\\.claude",
  "loginExpiresAt": "2026-12-12T03:35:57.587Z",
  "email": "<redacted>",
  "orgId": "<redacted>",
  "orgName": "<redacted>",
  "subscriptionType": "max",
  "storedClaudeAiLogin": true,
  "planTier": "max_20x"
}
```

CLAUDE*/ANTHROPIC* variables in the worker env: ['CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH']

## Drill: the detached child outlives the tool call that started it

Probe 1 above starts the parent inside the spike's own process. This drill starts it from one Claude Code
Bash tool call and checks from the next one, which is how the front desk will start the conveyor.

```
call 1 (00:03:32): python ship spike --program <this folder> --parent
  rc=0; child.pid = {"pid": 17148, "parent": 22004, "how": "detached"}
call 2 (00:03:36): pid_alive(22004) False; pid_alive(17148) True; tasklist shows python.exe 17148
call 3 (00:03:51): child.json written: kind ok, session_id equals the one passed, modelUsage ['claude-haiku-5-5']
```

PASS drill: the child and its claude run outlived both the parent and the tool call.
