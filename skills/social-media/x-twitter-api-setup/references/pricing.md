# X API Pay-Per-Use Pricing (2026)

Reference: https://docs.x.com/x-api/getting-started/pricing

## Per-Request Costs

| Operation | Price per request |
|-----------|------------------|
| Read your own post (owned read) | $0.001 per resource |
| Read a third-party post | $0.005 per resource |
| Read a user, following, followers, trends | $0.010 per resource |
| Create a text or media post (no URL) | $0.015 per request |
| **Create a post containing a URL** | **$0.20 per request** |
| Send a DM | $0.015 per request |
| User management (block, mute) | $0.015 per request |
| Delete a post | $0.010 per request |
| Follow, like, quote-post | $0.015 per request |
| Create a poll | same as post type (URL/no-URL) |

## Budget Planning

### $5 (minimum purchase)

| Strategy | Tweets without URL | Tweets with URL | Daily cost | Duration |
|----------|-------------------|-----------------|------------|----------|
| All text-only | ~333 | 0 | $0.15 (10/day) | ~33 days |
| Mix (10 text + 2 links/day) | ~10/day | ~2/day | $0.38/day | ~13 days |
| All with URL | 0 | ~25 | $2.00 (10/day) | ~2-3 days |

### Key Facts

- **24-hour deduplication**: Fetching the same post/user within a UTC day only charges once.
- **Per-resource pricing**: A single call returning 100 posts costs $0.005 × 100 = $0.50, not $0.005.
- **URL tax**: Posts with ANY URL cost 13× more than text-only posts.
- **Rate limits are separate from cost**: Credits don't lift rate limits.
- **2M reads/month cap**: Hard limit on post reads. Resets monthly.
- **xAI credit kickback**: Up to 20% back in xAI credits based on cumulative spend.
