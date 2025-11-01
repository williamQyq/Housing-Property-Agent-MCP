0) Scope (MVP-first)
Identity via SMS OTP (phone sign-in).
Room (group) creation & join with role = LANDLORD or TENANT.
Invite-by-phone deep-link flow.
BFF (Go) front door; Identity service; Orchestrator for rooms/invites; Python MCP for tool execution; Java Payments present but out-of-scope here.
ai-sdk-ui renders two key tools: Phone login and Room setup (role selection).https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces
LLM system prompt drives the guided flow inside the text panel.
1) Services
BFF (Go)
Edge REST/GraphQL for UI; validates JWT/session; rate limiting & idempotency.
Orchestrates calls to Identity & Orchestrator.
Hosts tool endpoints invoked by ai-sdk-ui (server-only actions).
Propagates trace_id, user_id.
Identity Service (Go)
/otp/start and /otp/verify.
Creates user on first verification; issues JWT (or session cookie).
Stores OTP/session in Redis.
Sends OTP via Notification (or directly via Twilio in MVP).
Phone normalization (E.164), hash for lookups, encrypt raw phone at rest via KMS.
Orchestrator (Go)
Room/Group lifecycle and membership.
Invite-by-phone; accepts invite token; enforces role constraints.
Persists to Core Postgres (RLS by user_id).
Agent/MCP (Python)
Executes ai-sdk-ui tool calls from BFF with allowlisted tools.
Enforces safe inputs (PII masking, rate limits).
(Payments (Java) stays available for future flows but not used here.)
2) APIs (BFF Edge)
openapi: 3.0.3
info: {title: Identity & Rooms BFF, version: 0.1.0}
paths:
  /auth/otp/start:
    post:
      summary: Start OTP login
      requestBody:
        required: true
        content: {application/json: {schema: {type: object, properties: {phone: {type: string}}}}}
      responses: {"200": {description: "OTP sent if rate limits allow"}}

  /auth/otp/verify:
    post:
      summary: Verify OTP and create session
      requestBody:
        required: true
        content: {application/json: {schema: {type: object, required:[phone,code],
          properties: {phone:{type:string}, code:{type:string}}}}}
      responses: {"200": {description: "Authenticated", content:
        application/json: {schema: {type: object, properties: {user_id:{type:string}}}}}}

  /rooms:
    post:
      summary: Create a room (group) with caller’s role
      security: [{ bearerAuth: [] }]
      requestBody:
        content: {application/json: {schema: {type: object, required:[name, role],
          properties: {name:{type:string}, role:{type:string, enum:[LANDLORD,TENANT]}}}}}
      responses: {"201": {description: Created}}

  /rooms/{id}/invites:
    post:
      summary: Invite another user by phone with intended role
      security: [{ bearerAuth: [] }]
      parameters: [{name:id, in:path, required:true, schema:{type:string}}]
      requestBody:
        content: {application/json: {schema: {type: object, required:[phone,role],
          properties: {phone:{type:string}, role:{type:string, enum:[LANDLORD,TENANT]}}}}}
      responses: {"201": {description: Invite created (deep link SMS queued)}}

  /invites/{token}/accept:
    post:
      summary: Accept invite after OTP login
      security: [{ bearerAuth: [] }]
      responses: {"200": {description: Joined room}}
(BFF forwards to Identity /otp/* and to Orchestrator /rooms/* internally.)
3) Internal APIs (service-to-service)
Identity
POST /otp/start { phone } → 200
POST /otp/verify { phone, code } → { user_id, jwt, expires_at }
Orchestrator
POST /rooms { name, creator_user_id, role } → { room_id }
POST /rooms/{id}/invites { phone, role, inviter_user_id } → { invite_id, token }
POST /invites/{token}/accept { user_id } → { membership_id }
4) Data Model (Core Postgres)
create table users (
  id uuid primary key default gen_random_uuid(),
  phone_e164 text not null,          -- encrypted with KMS
  phone_hash bytea not null unique,  -- SHA-256(e164 + salt)
  created_at timestamptz default now()
);

create type role as enum ('LANDLORD','TENANT');

create table rooms (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_user_id uuid not null references users(id),
  created_at timestamptz default now()
);

create table room_memberships (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references rooms(id),
  user_id uuid not null references users(id),
  role role not null,
  created_at timestamptz default now(),
  unique (room_id, user_id)
);

create table invites (
  id uuid primary key default gen_random_uuid(),
  room_id uuid not null references rooms(id),
  phone_e164 text not null,          -- encrypted
  role role not null,
  token uuid not null,
  status text not null default 'PENDING',
  expires_at timestamptz not null,
  created_at timestamptz default now()
);
RLS (illustrative)
Enable RLS on rooms, room_memberships, invites; set app.user_id on each DB session; policies allow read/write only to a user’s own memberships and invites.
5) Flows (happy paths)
A) Phone login (anonymous → authenticated)
ai-sdk-ui asks for phone → BFF /auth/otp/start.
Identity generates OTP → store in Redis (TTL 5 min; attempt counter); send SMS via Twilio.
User enters code → BFF /auth/otp/verify → Identity validates; creates user (if first) → returns JWT.
BFF sets HTTP-only secure cookie or returns bearer token.
B) Create a room with role & invite
User selects role (LANDLORD/TENANT) + room name → BFF /rooms.
Orchestrator creates room + membership for the creator.
User enters invitee phone + role → BFF /rooms/{id}/invites.
Orchestrator creates invite (token), triggers SMS (via Notification/Twilio) with deep link.
Invitee opens link → OTP login if needed → BFF /invites/{token}/accept → Orchestrator adds membership.
6) ai-sdk-ui Tools (phone + role)
Tool Registry (JSON)
[
  {"name":"auth.startOtp","inputs":{"phone":"string"},"auth":"anon"},
  {"name":"auth.verifyOtp","inputs":{"phone":"string","code":"string"},"auth":"anon"},
  {"name":"rooms.create","inputs":{"name":"string","role":"LANDLORD|TENANT"},"auth":"user"},
  {"name":"rooms.inviteByPhone","inputs":{"room_id":"string","phone":"string","role":"LANDLORD|TENANT"},"auth":"user"},
  {"name":"invites.accept","inputs":{"token":"string"},"auth":"user"}
]
UI components
Phone Login Tool Panel
Field: phone (E.164, client-side formatting)
Button: “Send code” → calls auth.startOtp
Field: code (6 digits) → calls auth.verifyOtp
Room Setup Tool Panel
Fields: room name, role selector (LANDLORD/TENANT)
Button: “Create Room” → calls rooms.create
Fields: invite phone, role selector
Button: “Send Invite” → calls rooms.inviteByPhone
Validation
Mask phone display as ***-***-1234
Enforce unique membership per room; role required.
7) System Prompt for LLM (MVP)
You are the in-app concierge for identity and room setup.

State:
- auth_state: ANON | AUTHENTICATED
- user_profile: { user_id?, rooms[] }
- tools: auth.startOtp, auth.verifyOtp, rooms.create, rooms.inviteByPhone, invites.accept

Rules:
1) If auth_state == ANON:
   • Ask the user for their phone number.
   • On phone: call auth.startOtp(phone). Then ask for the 6-digit code.
   • On code: call auth.verifyOtp(phone, code). If success, continue to step 2.
   • Never reveal whether a phone exists in our system.

2) If the user has no rooms:
   • Suggest creating a room and selecting their role (LANDLORD or TENANT).
   • Show the Room Setup tool panel.
   • On submit: call rooms.create(name, role).
   • Then offer to invite the other party by phone: call rooms.inviteByPhone(room_id, phone, role).

3) If the user clicked a deep-link token:
   • Ensure they are authenticated first.
   • Call invites.accept(token) to join the room.

General:
- Keep messages brief; prefer showing the appropriate tool panel.
- Mask phone numbers in responses.
- Do not send arbitrary SMS text; the system uses templates.
- If a tool call fails, briefly explain and offer a retry.
8) Security & Abuse Controls (MVP)
OTP: 6 digits, TTL 5 minutes, max 5 attempts, device/IP cooldown.
Normalize to E.164; store phone_hash for lookups; encrypt phone_e164.
Do not confirm if a phone is registered (generic success message on /otp/start).
Rate-limit /auth/otp/start and /auth/otp/verify.
JWT rotation endpoint (/auth/refresh) optional for MVP.
All endpoints log JSON with trace_id, redacted PII.
9) Deployment Quick Notes
K8s: BFF, Identity, Orchestrator, MCP each as a Deployment; Postgres/Redis managed.
Ingress (Nginx/Envoy) with strict CORS; HPA on BFF.
Secrets via External Secrets Operator; KMS for app-layer encryption keys.
OTEL instrumentation on BFF, Identity, Orchestrator.
10) Minimal Acceptance Tests
OTP sign-in: happy path; wrong code lockout; masking.
Create room: role required; self-membership created.
Invite: deep-link SMS simulated; accept flows both (new and existing users).
RLS: user cannot read/join rooms they don’t belong to.