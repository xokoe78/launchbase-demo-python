# Briefly — Python

A client-request portal with a polished landing page, registration, login, password recovery, private database records and a real test-email button. Same app, same design, same schema as the other language version.

[Get the other version](https://launchbase.build/demos) · [Launchbase documentation](https://launchbase.build/docs)

## Make your first app: your coding agent + Launchbase

1. Download this repository or the archive at https://launchbase.build/demos and extract it.
2. Open the folder in your coding agent (for example Cursor or Claude Code).
3. Paste this prompt:

> Read AGENTS.md and https://launchbase.build/agent.md. Connect to my Launchbase account or help me create one, then configure and deploy this template as a new app using the included schema and runtime setup instructions. Verify login, private requests and the test email, give me the live URL, and ask what I want to change.

4. Open the approval link from your agent. Create or sign in to your Launchbase account and approve the connection.
5. Tell the agent what your app should become. It applies the database schema, configures services and deploys. Open the URL it gives you.

The source is free under the MIT licence. Launchbase hosting uses its available trial and then a paid plan; provider costs are not waived by this licence. Your agent should explain any required paid action before proceeding.

## Run locally

Set the variables listed in `.env.example`. Next.js reads an untracked `.env.local`; Python reads environment variables from your shell (it does not automatically load .env). Set APP_ORIGIN to your actual local URL, without a trailing slash, and PORT to its port.

```sh
python -m venv .venv
# Activate .venv for your operating system
pip install -r requirements.txt
python app.py
```

Visit http://localhost:3000. Without Supabase configured, the landing page and guide work but auth/database calls explain the missing setup. There is no fake local login.

Apply `schema.sql` to your own development Supabase database, and allow `http://localhost:3000/callback` and `/reset` as auth redirects. Use a public/anon key, never a service-role key. Keep email confirmation enabled. Configure Supabase's auth email delivery for registration/recovery; transactional test email uses Launchbase separately.

## What Launchbase configures

| Variable | Purpose |
|---|---|
| SUPABASE_URL | This app's database/auth endpoint |
| SUPABASE_ANON_KEY | Public API key, restricted by RLS |
| APP_ORIGIN | Exact app URL, used for origin checks and auth redirects |
| PORT | Web server port |
| LB_RUNTIME_URL | Launchbase runtime endpoint |
| LB_RUNTIME_TOKEN | Server-only app token for verified-user test emails |

Your agent calls `POST /api/v1/apps/{id}/runtime` after provisioning to inject runtime access. Secret values are not returned. These variables take effect on the next deployment. You do not need Railway, Resend or Supabase management keys in the app.

For local testing, use a development database and test the email button on your deployed app. Do not copy your agent management token into LB_RUNTIME_TOKEN. BYOK email accounts are configured in Launchbase, not embedded into frontend code.

## Check it works

- Register and follow the confirmation email. Log in, create a request, refresh and confirm it persists.
- Change its status. Filter requests. Delete a disposable request.
- Sign in as a second user: the first user's requests must not appear. Direct database access with that user's token must also be isolated by RLS.
- Use Forgot password and follow the reset link. Choose a new password.
- Send a test email: it goes only to your verified address, at most three attempts per day, within the app allowance.
- Log out: requests are no longer accessible. GET /api/health verifies the server, not the full provider chain.

## Files and deployment

`schema.sql` is the shared database migration. `AGENTS.md` contains the complete agent setup steps. `PROMPT.md` is ready to paste. UI assets live in `public/`; API logic lives in app.py. The app is one web service with external persistent storage. Do not use the container filesystem for user data.

Procfile runs Gunicorn on 0.0.0.0:$PORT. Use Gunicorn in production; python app.py is for local development.

Public showcase visitors should only enter sample data. This template intentionally has no payment collection, shared team access or file uploads. Those require additional product-specific rules and tests.

## Adding payments
This template does not enable customer billing by default. Read https://launchbase.build/docs/payments.md to add managed checkout, plans, saved cards, subscriptions, invoices, events and paid access. Your backend uses the app-only LB_RUNTIME_TOKEN, derives customerRef from its verified user session, and keeps credentials server-only. Start in test mode; the owner activates live payments. No Stripe secret key is needed in managed mode. Test customer isolation and cancellation before launch.
