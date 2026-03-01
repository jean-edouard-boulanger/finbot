  Critical — Security & Data Loss                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                          
  ┌─────┬─────────────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐                                                               
  │  #  │                 Gap                 │                                                                  Detail                                                                   │                                                               
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                               
  │ 1   │ Secrets committed to repo           │ secrets.dev.env and secrets.prod.env contain live API keys (Plaid, Twilio, GoCardless, FreeCurrencyAPI, Fernet keys). Rotate immediately. │                                                               
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                               
  │ 2   │ No database backups                 │ No pg_dump automation, no snapshot export, no restore procedure. Disk failure = total data loss.                                          │                                                               
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                               
  │ 3   │ No TLS anywhere                     │ nginx serves HTTP only. Financial credentials and JWT tokens transit in plaintext.                                                        │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 4   │ CORS wide open in prod              │ allow_origins=["*"] with allow_credentials=True. Any origin can make authenticated requests.                                              │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 5   │ Stack traces in API responses       │ ApplicationErrorData.from_exception() unconditionally includes full tracebacks — leaks file paths, library versions, call stacks.         │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 6   │ Temporal UI/port exposed in prod    │ Port 5006 (Temporal UI) and 7233 (Temporal gRPC) publicly accessible with no auth.                                                        │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 7   │ No rate limiting                    │ Zero throttling on login, account creation, or valuation trigger endpoints.                                                               │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 8   │ Email check leaks account existence │ GET /accounts/email_available/ is unauthenticated — enables account enumeration.                                                          │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 9   │ No token revocation                 │ Refresh token is minted but no refresh endpoint exists. No logout endpoint. Tokens valid for 24h regardless.                              │
  ├─────┼─────────────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 10  │ No RBAC                             │ Provider CRUD (global state) is accessible to any authenticated user. Admin pages shown to everyone.                                      │
  └─────┴─────────────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  High — Reliability & Data Integrity

  ┌─────┬──────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │  #  │                     Gap                      │                                                      Detail                                                      │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 11  │ PostgreSQL 12 is EOL                         │ End-of-life since Nov 2024. No security patches.                                                                 │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 12  │ Failed snapshots stuck in Processing         │ If build_and_persist_final_snapshot throws, the snapshot row is never marked Failure.                            │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 13  │ get_financial_data called twice per provider │ The workflow calls the activity once (discards result), then calls again. Doubles API calls and browser scrapes. │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 14  │ TRY_ONCE everywhere                          │ All Temporal retry policies are maximum_attempts=1. Single transient error permanently fails the workflow.       │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 15  │ schedule_valuation flag is ignored           │ get_ids_of_user_accounts_that_need_valuation() queries all users — the opt-out flag is never checked.            │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 16  │ FX rate cache is not thread-safe             │ cachetools.cached with TTLCache but no Lock. Concurrent Temporal threads can corrupt the cache.                  │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 17  │ No request timeout on FX API                 │ requests.get() to freecurrencyapi.com has no timeout — can hang a worker thread indefinitely.                    │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 18  │ No restart policy in prod compose            │ Missing restart: always on most containers. Host reboot = services stay down.                                    │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 19  │ Missing DB indexes                           │ No indexes on linked_accounts.user_account_id, snapshots.linked_account_id, or any valuation history FKs.        │
  ├─────┼──────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 20  │ No migrations on deploy                      │ No alembic upgrade head in any entrypoint. Schema changes require manual intervention.                           │
  └─────┴──────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  High — UX & Frontend

  ┌─────┬────────────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │  #  │            Gap             │                                                                    Detail                                                                     │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 21  │ Silent failures everywhere │ Dashboard, linked account dashboard, charts, and sidebar all swallow errors — user sees infinite skeleton or empty state with no explanation. │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 22  │ No data refresh            │ Dashboard valuation fetched once on mount, never refreshed. No "last updated" timestamp, no refresh button, no auto-refresh.                  │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 23  │ Onboarding is nearly empty │ Welcome page is two sentences. No guided wizard, no post-link-account "waiting for first sync" feedback, no progress indicator.               │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 24  │ No empty states            │ Charts, holdings table, and earnings report render blank when there's no data — no "No data yet" messages.                                    │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 25  │ Charts hide both axes      │ X-axis and Y-axis are explicitly hidden. Users can only read values via tooltips.                                                             │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 26  │ No export capability       │ No CSV, PDF, or JSON export for any financial data. No print stylesheet.                                                                      │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 27  │ No search or filtering     │ Zero search inputs across the entire app. Holdings tree can't be filtered. Earnings report has no date range selector.                        │
  ├─────┼────────────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 28  │ Hardcoded locale           │ "en-GB" hardcoded for number/date formatting. US/French/etc. users see British formatting.                                                    │
  └─────┴────────────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Medium — Missing Features

  ┌─────┬─────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │  #  │               Gap               │                                                     Detail                                                     │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 29  │ No valuation currency change    │ Set at signup, no way to change it. No API endpoint exists for updating settings.                              │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 30  │ No account deletion             │ No DELETE /accounts/ endpoint. No "Delete my account" in Settings. GDPR concern.                               │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 31  │ No data retention/purge         │ 6 snapshots/day accumulate forever. No compaction, no archival, no cleanup job.                                │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 32  │ No sub-account filtering        │ selected_sub_accounts field exists in the model but no API endpoint to configure it.                           │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 33  │ No notification preferences     │ Users can't opt in/out of emails or configure notification frequency.                                          │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 34  │ No session management           │ Can't see active sessions, revoke tokens, or view last login. No 2FA.                                          │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 35  │ No observability                │ No Prometheus metrics, no structured logging, no distributed tracing (was removed), no request IDs.            │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 36  │ Test coverage near zero         │ System tests = 1 smoke test. No tests for auth, valuation routes, JWT flow, reports, or providers.             │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 37  │ react-select ignores dark theme │ Email delivery dropdown is stark white in dark mode. AceEditor same — uses github (light) theme always.        │
  ├─────┼─────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ 38  │ Filter state not in URL         │ Chart grouping, frequency, time range, distribution mode — none persist in the URL. Refresh resets everything. │
  └─────┴─────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Medium — Accessibility

  ┌─────┬─────────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────────────┐
  │  #  │                 Gap                 │                                       Detail                                        │
  ├─────┼─────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ 39  │ ColourPicker is a div, not a button │ No role, no aria-label, no keyboard support.                                        │
  ├─────┼─────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ 40  │ TreeGrid expander is a span         │ No aria-expanded, no keyboard navigation. Screen readers can't expand/collapse.     │
  ├─────┼─────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ 41  │ Icon-only buttons lack aria-labels  │ MoreHorizontal dropdown trigger, inline edit button — unlabeled for screen readers. │
  ├─────┼─────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ 42  │ No page title updates               │ Browser tab always shows the static HTML title. Can't distinguish tabs.             │
  ├─────┼─────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────┤
  │ 43  │ Login email field is type="text"    │ Mobile keyboards don't show @-optimized layout.                                     │
  └─────┴─────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────┘

  ---
  Lower Priority — Polish

  ┌─────┬─────────────────────────────────┬─────────────────────────────────────────────────────────────────────────────┐
  │  #  │               Gap               │                                   Detail                                    │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 44  │ No breadcrumbs                  │ No hierarchical context anywhere.                                           │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 45  │ No prev/next account navigation │ Must go back to sidebar to switch between accounts.                         │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 46  │ No 404 page                     │ Unmatched routes silently redirect.                                         │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 47  │ Logout is a render side-effect  │ No confirmation dialog. logout() called during React render.                │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 48  │ Pie segments not clickable      │ Could navigate to account dashboard on click.                               │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 49  │ Legend hidden on mobile         │ useShowLegend hides chart legend below 765px. Pie charts become unreadable. │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 50  │ No changelog                    │ No release notes, no CONTRIBUTING.md, README references old service names.  │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 51  │ package-lock.json gitignored    │ Non-deterministic frontend builds.                                          │
  ├─────┼─────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────┤
  │ 52  │ Dead dependencies               │ celery in pyproject.toml but unused. oauth2client is deprecated.            │
  └─────┴─────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────┘

  ---
  The biggest bang-for-buck improvements would be: error handling + data refresh (items 21-22, most user-visible), TLS + CORS (items 3-4, most dangerous), and database backups (item 2, most catastrophic if neglected). Want me to prioritize a roadmap
  or start tackling any of these?
