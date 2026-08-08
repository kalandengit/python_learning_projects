# VPS deployment

1. Copy `.env.example` to `.env`.
2. Set a new domain/subdomain and strong secrets.
3. Run `scripts/preflight.sh`.
4. Run `scripts/deploy.sh`.
5. Point DNS to the VPS.
6. Run `scripts/install-nginx.sh`.
7. Create an Odoo database through the normal controlled setup path.
8. Run `scripts/install-modules.sh DATABASE`.
9. Validate backup/restore before launch.

The Odoo port is loopback-only by design so this stack can coexist with other services behind host Nginx.
