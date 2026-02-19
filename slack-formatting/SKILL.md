---
name: slack-formatting
description: Format content for Slack posts. Use when writing Slack messages, announcements, updates, or converting content from other formats (email, Notion, docs) to Slack-friendly formatting. 
---

# Slack Formatting

Format content optimized for Slack's reading experience. We did it!

## Core Rules

1. **Lead with context**: Start every post with a friendly one-sentence summary so readers immediately know what this is about

2. **No dashes**: Avoid em dashes (—), en dashes (–), and hyphens used as punctuation. Use periods, semicolons, or colons instead
   - ❌ "The project is delayed — we need more time"
   - ✅ "The project is delayed; we need more time"
   - ✅ "The project is delayed: we need more time"

3. **Single asterisk for bold**: Use `*text*` not `**text**`
   - ❌ `**important**`
   - ✅ `*important*`

4. **Keep formatting minimal**: Only use bolding, underscores (`_italic_`), and bullets. Avoid headers, numbered lists, and complex nesting

5. **Be brief**: Slack is for quick consumption. Cut unnecessary words; get to the point

## Quick Reference

| Element | Slack Syntax |
|---------|--------------|
| Bold | `*text*` |
| Italic | `_text_` |
| Strikethrough | `~text~` |
| Code | `` `code` `` |
| Link | `<url|display text>` |
| Bullet | `• ` or `- ` |

## Example

**Input request**: "Write a project update about the API migration being complete"

**Slack output**:
```
Quick update: the API migration is now complete and live in production.

*What shipped*
• New REST endpoints are active
• Legacy endpoints deprecated (sunset in 30 days)
• Response times improved by 40%

*Action needed*
• Update your integrations to use v2 endpoints
• Questions? Drop them in #api-support
```
