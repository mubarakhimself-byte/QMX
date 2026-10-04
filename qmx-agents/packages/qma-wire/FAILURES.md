# qma-wire SDK request failures

This register covers the proposed optional authenticated SDK methods; existing wire refusal contracts remain authoritative. No new failure category or authority store is created.

## FR-SDK-W01: Missing host method capability

- **Failure class:** policy rejection.
- **Detection:** each submit/get/cancel method requires its own server-advertised capability after existing paired initialization.
- **Auto-recovery / retry:** none; a client advertisement cannot enable a disabled SDK.
- **Visible degraded state:** typed method-capability refusal, no request execution.
- **Notification tier:** wire response.
- **Product-user affordance:** connect to a host where the requested SDK profile/service is configured.

## FR-SDK-W02: Invalid request DTO or UTF-8 text

- **Failure class:** invalid input.
- **Detection:** exact string-keyed fields, bounded namespaced session/request identities, bounded nonempty prompt/idempotency key and UTF-8 encoding validity. Lone surrogates are refused rather than raising from the parser.
- **Auto-recovery / retry:** none; correct the payload.
- **Visible degraded state:** typed refusal; no provider/principal/grant/instruction injection field is accepted.
- **Notification tier:** wire response without echoing prompt contents.
- **Product-user affordance:** submit a valid prompt using a host-installed profile and existing ProductSession reference.

## FR-SDK-W03: Authentication/session ownership mismatch

- **Failure class:** policy rejection.
- **Detection:** existing paired origin/proof and operator admission precede dispatch; daemon checks canonical principal plus exact originating ProductSession for status/cancellation.
- **Auto-recovery / retry:** none; no request-ID-only disclosure or cancellation.
- **Visible degraded state:** typed refusal. Authorized originating status remains safe when content disclosure is withheld after narrowing.
- **Notification tier:** wire response.
- **Product-user affordance:** use the originating authorized session; pairing does not mint a new multi-user identity model.

### FR-SDK-W04: Explicit resume rejected

- **Failure class:** policy rejection.
- **Detection:** Resume requires negotiated operator capability, original session/principal, current host policy/grants and an interrupted request; queue must have capacity.
- **Auto-recovery / retry:** No automatic retry.
- **Visible degraded state:** Typed refusal; no scope widening or unauthorized inference.
- **Notification tier:** sanitized operator request/wire response.
- **Product-user affordance:** Resume the original authorized interrupted request once capacity and scope permit; resumption can repeat an unknown model call.
