# Worked Example: ReverseLookup.com Audit

Audited 2026-07-13. Full report delivered in French to the user.

## URLs found
- Terms & Conditions: `/terms-conditions` (updated 2026-06-24)
- Privacy Policy (EU/UK): `/privacy-policy`
- Cookie Policy: `/cookie-policy`
- Dead (404): `/terms`, `/privacy`, `/legal`, `/terms-of-service`, `/terms-of-use`, `/tos`

## Key URLs discovered
- Opt-out phone: `/en/settings/exclude-phone`
- Opt-out email: `/en/settings/exclude-email`
- Account deletion: `/en/settings/delete`
- Cancellation: `/cancellation`
- Pricing: `/pricing`

## Company
ClarityCheck Inc., 2093 Philadelphia Pike #7776, Claymont, DE 19703, USA  
DPO: dpo@reverselookup.com  
Privacy: privacy@reverselookup.com  
Help: help@reverselookup.com

## Doc sizes
- Terms & Conditions: ~91 KB, 674 lines — needed read_file pagination (offset=1, 201, 401, 601)
- Privacy Policy: ~15 KB — fit in single web_extract
- Cookie Policy: ~8 KB — fit in single web_extract

## Cookie highlights
- Customer.io `_cio`: 20 year lifetime (huge red flag)
- Google Analytics `_ga`: 2 years
- Mixpanel: 1 year
- Facebook/Pinterest/TikTok ads: 3 months–1 year

## Cached Reports retention
120 days, then auto-deleted. Optional feature.

## Governing law
Delaware, USA — class action waiver + binding AAA arbitration.
