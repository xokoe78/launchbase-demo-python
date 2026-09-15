# Deploy Briefly with Launchbase

This is a complete client-request portal, not a mock login. Preserve the working auth, server-only cookies and database isolation when adapting it.

## Before changing anything
Read https://launchbase.build/agent.md, https://launchbase.build/api/v1/guide and https://launchbase.build/api/v1/openapi.json. Use the current documented API shapes and owner approvals. Do not treat this file as permission to spend or delete data.

## Connect and create
1. Reuse your Launchbase connection. Otherwise use POST /api/v1/agent/connect for an existing account, or the documented agent signup flow. Show the owner the approval URL and wait. Store the management credential outside this repository, never in the deployed app.
2. Ask for the app name and intended changes. Create a new app only if requested; never overwrite an existing app without instruction. Set config.start="existing", config.region="eu-west", and config.components hosting/database/auth/email to "managed". Payments/domain/AI are optional and not required by this demo.
3. Start the available trial with POST /api/v1/projects/{id}/billing/trial. If eligibility requires owner action, show the returned link. The source is free; hosting has a limited trial and paid plans. Do not claim perpetual free hosting or silently purchase a plan.
4. Poll app/jobs until hosting, database, auth and email are ready. Explain action_required responses. Apply schema.sql through POST /api/v1/projects/{id}/database/migrations with name "briefly_001" and the exact SQL content. Both languages use the same schema. Keep RLS and the auth.uid() policies.
5. POST /api/v1/projects/{id}/runtime with {}. This injects LB_RUNTIME_URL and LB_RUNTIME_TOKEN directly into hosting; it never returns the secret. The app-only token can send a fixed test email to a verified user of THIS app. It cannot manage infrastructure. Do not use your agent token instead.
6. Launchbase supplies SUPABASE_URL, SUPABASE_ANON_KEY, APP_ORIGIN and PORT. Confirmation/recovery links must allow APP_ORIGIN/callback and APP_ORIGIN/reset in the app's Supabase auth redirect settings. Managed provisioning allows the app origin. Use the documented auth settings route if changing domains.
7. Validate source, upload and deploy using the current guide. Exclude .git, .env*, node_modules, .next, .venv and caches. Health path /api/health. Do not upload this file as a substitute for the actual source. Poll the release; inspect build/runtime logs on failure.
8. Verify the public landing page and /guide. Create disposable test users through the normal auth flow, test sign-in/out, persistence, request status changes, password recovery and the email button. Ask the owner to follow inbox links or enter their own credentials. Never report inbox delivery from a successful send response alone. Confirm user A cannot see/update/delete user B's rows. Do not disable email verification to make tests pass.
9. Return the live app URL and the exact checks performed. Ask what to customise next.

## Runtime security and behaviour
- Supabase public key is intentionally unprivileged. Queries use the signed-in user's access token, never service-role or database-admin credentials.
- Cookies are HttpOnly, SameSite=Lax, Secure on HTTPS; writes require the exact APP_ORIGIN. Local HTTP uses non-__Host cookie names.
- The email button sends only to the authenticated, verified user's email. Launchbase enforces 3 requests per user per day and the app's email allowance. No arbitrary recipient or HTML is accepted by this runtime capability.
- Management credentials and provider master keys must never be included in public source, client JS, screenshots, logs or environment examples.
- This demo does not include payments, file storage or team invitations. Add those deliberately, with the documented ownership, access and payment flows; do not present them as already implemented.
- Show real loading, empty and error states. Do not swap database calls for localStorage or fake success when a provider fails.

## Adaptation map
UI: public/portal.js and portal.css; Next.js also has app/markup.js and app/style.css.
Schema: schema.sql. API: Next.js app/api/[...path]/route.js or Python app.py.
The /guide page is written for humans and includes the setup prompt.
