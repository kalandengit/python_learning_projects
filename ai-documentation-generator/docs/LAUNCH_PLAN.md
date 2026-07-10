# Sprint 12 Launch Plan

## Objective
Prepare DocuPilot AI for a controlled private beta and a public Product Hunt launch.

## Beta launch criteria
- Production Vercel deployment is connected to a non-local Supabase project.
- Stripe test mode is validated, then live mode is configured.
- OpenAI key is set and generation costs are monitored.
- Public pages exist: pricing, security, privacy, terms, beta, contact.
- Feedback submissions are captured in `feedback_submissions`.
- At least 10 design partners are invited before public launch.

## Launch sequence

### Week -2
- Recruit 10-20 beta users from SaaS teams, agencies, customer support teams, and product managers.
- Record 5 end-to-end demo videos using realistic screenshot workflows.
- Create 3 sample documents: onboarding guide, SOP, and help article.
- Validate upload, generation, editing, export, sharing, and billing flows.

### Week -1
- Freeze core product scope.
- Fix onboarding friction.
- Prepare Product Hunt assets.
- Publish security and legal placeholder pages after counsel review.
- Set monitoring alerts in Sentry and PostHog.

### Launch day
- Launch Product Hunt listing at midnight Pacific time.
- Reply to every comment within 30 minutes during the first 12 hours.
- Share short demo videos on LinkedIn, X, Reddit, and founder communities.
- Route all feedback into `feedback_submissions` and tag issues by severity.

### Week +1
- Follow up with all trial signups.
- Publish launch learnings.
- Convert beta users into annual customers or design partners.
- Prioritize fixes by activation and retention impact.

## Risks
- AI output quality varies by screenshot clarity.
- PDF generation can require browser dependencies in production.
- Public beta forms need spam/rate limiting before large-scale promotion.
- Legal pages are placeholders until reviewed.

## Success metrics
- 100+ waitlist or beta signups.
- 25+ activated users.
- 10+ generated documents exported.
- 5+ customer discovery calls booked.
- 3+ paid pilot conversations.
