# Security Standards

**Principle**: Assume failure modes exist, then design so they're boring when they happen. Security effort should be proportionate to the workflow phase and architecture — prototype code needs basic hygiene; production code needs defence in depth.

**Mental shortcut**: For any security decision, ask: *if a mistake happens here, does it fail closed, loudly, and recoverably?* If yes, you're in good shape.

---

## Phase-Proportionate Security

Not every phase needs the same rigour. Match security investment to risk:

| Concern | Prototype | Production |
|---------|-----------|------------|
| Authentication | API keys, simple tokens | JWT/OAuth with refresh, RBAC |
| Input validation | Schema validation on boundaries | Schema validation everywhere + sanitisation |
| Secrets | Local files, not committed | Secret manager (e.g. GCP Secret Manager) |
| Dependencies | Pin versions | Pin + audit + automated updates |
| Logging | Console output | Structured logging, no PII in logs |
| HTTPS | Optional locally | Enforced everywhere |

**Rule of thumb**: If you wouldn't deploy it to users, you can defer hardening. But never defer: secrets hygiene, input validation at boundaries, and dependency pinning.

---

## Boundaries

Every boundary is hostile until proven otherwise: HTTP requests, environment variables, message queues, browser inputs, config files. Code inside a trust boundary can trust its neighbours; code at the boundary must validate everything.

**Internal backend (e.g. Cloud Run behind VPC)**:
- Network-level isolation already provided by the platform
- Service-to-service auth can use platform identity (e.g. GCP IAM, workload identity)
- No need to re-implement network security that the platform provides

**Public frontend (e.g. Firebase Hosting)**:
- Assume the browser is compromised. Never trust client-side validation.
- CSP headers, CORS policies, CSRF protection, and HTTPS are mandatory
- Escape output by default; avoid dangerously setting HTML

**Key principle**: Rely on platform security where it exists. Don't rewrite what your cloud provider already enforces. Document which security guarantees come from infrastructure vs application code.

---

## Input Validation

Validate at system boundaries. Trust internal code and framework guarantees. Types stop developers; schemas stop attackers — compile-time types aren't enough for runtime safety.

**Principles**:
- Validate all external input (user input, API requests, webhook payloads) with runtime schema validation
- Use schema validation libraries (Zod, Pydantic, JSON Schema) rather than manual checks
- Reject invalid input early with clear error messages
- Never trust client-side validation alone

**Anti-pattern**: Validating data that has already been validated upstream, or adding defensive checks inside trusted internal functions.

---

## Authentication & Authorisation

**See [tech-standards.md §Authentication Architecture](tech-standards.md#authentication-architecture) for implementation patterns (Firebase Auth, workload identity, token flows).**

### Security Principles

**Phase-Appropriate Auth**:
- **Prototype/spike**: API keys or simple bearer tokens are sufficient. Focus on proving the feature, not hardening auth.
- **Production**: Use established auth libraries and managed services. Never roll your own auth.

**Core Principles**:
- Use well-maintained auth libraries — never roll your own JWT verification, password hashing, or session management
- Separate authentication (who are you?) from authorisation (what can you do?). Different concerns, different boxes.
- Make authorisation explicit and centralised. Check permissions at the boundary, not deep in business logic. Deny by default.
- Apply least-privilege: default to no access, grant explicitly
- Token expiry and refresh should be handled by the auth library, not custom code
- For passwords: salted, slow hashes (bcrypt, scrypt, argon2). Never invent your own.

**Architecture Security**:
- Prefer platform identity (workload identity, service accounts) over shared secrets for service-to-service auth
- Machines should borrow credentials briefly, not store them
- Third-party API credentials: Use secrets management, rotate on schedule

---

## API Security

Different APIs have different threat profiles. Don't apply a one-size-fits-all policy.

### User-Facing APIs

| Concern | Approach |
|---------|----------|
| Rate limiting | Per-user/IP throttling; use platform or library (e.g. rate-limiter-flexible) |
| CORS | Explicit allow-list of origins; never `*` in production |
| Input size | Enforce request body limits |
| Auth | Token-based with expiry |

### Internal APIs (service-to-service)

| Concern | Approach |
|---------|----------|
| Auth | Platform identity (IAM, service accounts); no user-facing tokens |
| Rate limiting | Generally unnecessary behind VPC; monitor for runaway loops |
| Input validation | Schema validation on contract boundaries |

### LLM/AI APIs

LLM APIs have a distinct threat profile — token cost and prompt injection matter more than traditional rate limiting.

| Concern | Approach |
|---------|----------|
| Token budgets | Set max_tokens per request; monitor cumulative spend; alert on anomalies |
| Prompt injection | Never interpolate untrusted user input directly into system prompts |
| Output validation | Validate and sanitise LLM output before using in downstream logic |
| Model selection | Use cheaper models for low-risk tasks; reserve expensive models for high-value work |
| Timeouts | Set aggressive timeouts; LLM calls can hang indefinitely |

**Prompt injection defence**:
- Separate system instructions from user content with clear delimiters
- Treat all user-provided text as data, not instructions
- Validate LLM output against expected schemas before acting on it
- Log prompts and completions for audit (redact PII)

---

## Safe Failure

**See [coding-standards.md §Error Handling & Safe Failure](coding-standards.md#error-handling--safe-failure) for implementation patterns.**

Core principle: Errors must fail closed, loudly, and recoverably — without leaking secrets, stack traces, or internal structure.

**Security-specific considerations**:
- Never expose existence of resources to unauthorised users (404 vs 403 leaks information)
- Rate limit error responses to prevent enumeration attacks
- Sanitise all error messages at API boundaries — treat user-facing messages as untrusted output
- Default to denial: if anything unexpected happens, deny access rather than falling through to a permissive state

---

## Logging & Monitoring as Security

Logging is a security tool, not just an ops concern. Attackers are noisy; you just need ears.

**Log these security events**:
- Authentication attempts (success and failure)
- Permission denials
- Unusual spikes in traffic or error rates
- Configuration changes
- Input validation failures at boundaries

**Correlate with request IDs** so a single user journey can be traced across services.

**Alert on patterns**, not single events. One failed login is noise; fifty in a minute is signal.

**Never log**: passwords, tokens, PII, or request bodies containing sensitive data.

See [coding-standards.md §Logging Standards](coding-standards.md#logging-standards) for structured format and [tech-standards.md §Monitoring & Observability](tech-standards.md#monitoring--observability) for platform tooling.

---

## Data Security

### Data Classification

Know what you're handling and protect accordingly:

| Classification | Examples | Handling |
|---------------|----------|----------|
| Public | Marketing copy, docs | No special handling |
| Internal | Business logic, configs | Access control, don't expose publicly |
| Sensitive | User emails, usage data | Encrypt at rest, minimise retention |
| Restricted | Passwords, payment data, health records | Encrypt at rest and in transit, audit access, minimise collection |

### Principles

- **Minimise collection**: Don't collect data you don't need. Less data = less risk.
- **Minimise retention**: Delete data when it's no longer needed. Set retention policies.
- **Encrypt in transit**: HTTPS for all external communication. TLS for internal where crossing trust boundaries.
- **Encrypt at rest**: Use platform encryption (GCP default encryption, Firebase security rules). Don't store restricted data in plain text.
- **PII handling**: Never log PII. Redact or pseudonymise in non-production environments. Provide data export/deletion capability for user data.
- **Sanitisation**: Strip or encode user-generated content before rendering (prevents XSS). Use parameterised queries (prevents SQL injection).

### Anti-pattern

Building custom encryption, hashing, or anonymisation when the platform or a well-maintained library already provides it.

---

## Dependency Security

Prefer well-maintained libraries over custom security code. A mature library with thousands of users has been battle-tested in ways your custom code never will be.

**Principles**:
- Pin dependency versions and use lockfiles for reproducible builds
- Audit regularly for known CVEs
- Prefer libraries with active maintenance, security policies, and timely CVE responses
- Remove unused dependencies — they're attack surface with zero value
- Update dependencies on a regular cadence (monthly for non-critical, immediately for security patches)
- Treat "high severity but unreachable" as a tracked decision, not a shrug. The goal is not zero CVEs; it's zero *unknown* ones.

Dependencies are a supply chain, not free candy. Treat them accordingly.

**Anti-pattern**: Writing custom input sanitisation, crypto wrappers, or auth flows when a well-maintained library exists.

---

## Secrets Management

See [rules/secrets.md](../rules/secrets.md) for strict location matrices and constraints.

**Key points**:
- **Single source of truth**: Secrets exist in ONE place (`/secrets/` locally or Secret Manager in production). No duplication, no drift, easy rotation, clear audit trail.
- Never commit secrets to version control
- Never duplicate secrets across locations
- Rotate credentials on a schedule
- Use environment variables as transport, not storage — the real source is the secret manager
- Prefer identity-based auth (workload identity, OIDC) over shared secrets where the platform supports it
- Short-lived credentials over long-lived ones: machines should borrow credentials briefly and return them

### Loading Secrets Pattern

```python
# Python - correct
from pathlib import Path
import json

secrets_path = Path(__file__).parent.parent.parent / 'secrets' / 'supabase.json'
with open(secrets_path) as f:
    creds = json.load(f)
```

```typescript
// TypeScript - correct
import secrets from '../../../secrets/firebase.json';
```

---

## Testing Security

Automate your paranoia. Security tests age well because attack vectors don't go out of fashion.

- **Permission tests**: Unit tests for every authorisation check — verify that the wrong user *cannot* access the resource
- **Validator tests**: Property-based tests for input validators — throw random junk at schemas and confirm they reject it
- **"Evil user" tests**: Intentionally try the wrong thing — expired tokens, missing headers, oversized payloads, SQL in query params
- **Boundary fuzzing**: Fuzz inputs at API boundaries with unexpected types, lengths, and encodings
- **Threat modelling**: Even informal — ask "what happens if this endpoint is abused?" for every new API. The act of asking is more valuable than the diagram.

---

## Anti-Patterns

Common security mistakes to avoid:

| Anti-Pattern | Why It's Wrong | Do Instead |
|-------------|----------------|------------|
| Rolling your own auth | Crypto is hard; subtle bugs create exploits | Use established auth libraries/services |
| `CORS: *` in production | Allows any origin to make credentialed requests | Explicit allow-list of trusted origins |
| Catching all exceptions silently | Hides security-relevant errors | Catch specific exceptions; log failures |
| Interpolating user input into prompts | Enables prompt injection | Separate user data from instructions |
| Storing PII in logs | Compliance risk, data breach surface | Redact PII before logging |
| Custom encryption | Likely weaker than standard implementations | Use platform or library encryption |
| Validating only on the client | Trivially bypassed | Always validate server-side |
| Ignoring dependency audits | Known CVEs in your supply chain | Regular audits, automated alerts |
| Over-engineering security for prototypes | Wasted effort, slows iteration | Match rigour to phase (see table above) |

---

## Deployment Safety
<!-- applyTo: "**/{firestore.rules,firebase.json,*.config.*,package.json,pyproject.toml,lib/**,app/api/**}" -->
<!-- excludeAgent: "cloud-agent" -->

### Data Access & Permission Gates
- Flag database/Firestore security rules that permit unauthenticated writes or allow broad access without ownership checks (`allow write: if true;`).
- Flag backend routes modifying data without validating user authentication and authorization.
- **Input Validation**: Flag mutation routes (`POST`, `PUT`, `DELETE`) that accept external payloads without schema or field-level validation against unexpected/malicious input.

### Secrets & PII Leaks
- Flag hardcoded API keys, database credentials, or service accounts committed in code.
- Flag console logging or telemetry capturing sensitive PII (emails, passwords, tokens, payment data).
- Ensure client-exposed configs (`NEXT_PUBLIC_*`) do not contain private secrets.

### Supply Chain & Dependencies
- Flag newly added dependencies with known critical CVEs or suspicious, near-zero download typosquats.
