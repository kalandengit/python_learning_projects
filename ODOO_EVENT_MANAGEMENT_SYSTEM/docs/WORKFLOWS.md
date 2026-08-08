# Workflows

## Ticket
registration -> ticket active -> rotate/transfer/revoke -> scan -> used

## Waitlist
waiting -> offered -> accepted | expired | cancelled

## Seat
available -> temporary hold -> assigned -> released
Expired holds return to available through cron.

## Scanner
device enrolled -> event assigned -> active -> validate -> scan log
Revoked devices cannot accept scans.

## Payment
Odoo payment transaction -> done -> EMS payment link reconciled -> ticket issuance hook

## GDPR
request created -> validate scope -> export/anonymize -> completed
