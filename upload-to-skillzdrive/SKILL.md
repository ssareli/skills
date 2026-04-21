---
name: upload-to-skillzdrive
description: Upload a local .zip or .skill file to your SkillzDrive. Includes a bash script that must be run locally, using a short-lived upload ticket minted via MCP. No API key is embedded in the script.
tags: [utility, upload, skillzdrive, file-transfer]
execution_tier: local
---

# Upload to SkillzDrive

This skill uploads a local `.zip` or `.skill` file to the user's SkillzDrive. Authentication is via a short-lived single-use upload ticket minted from the current MCP session — nothing sensitive lives in the script itself.

## Step-by-Step Workflow

### Step 1: Mint an upload ticket

Call the `skills_createUploadTicket` MCP tool. If the user mentioned a specific collection, pass its name via `collectionName`; otherwise the ticket targets the caller's default (the current collection for scoped API keys, the drive for unscoped keys).

The response contains:

- `uploadToken` — an opaque `ut_live_…` bearer. Single-use, expires in 10 minutes.
- `uploadUrl` — the server endpoint the script posts to.
- `targetType` — `drive` or `collection`. If `collection`, the uploaded skill will be added to the caller's collection automatically.
- `websiteFallbackUrl` — present only for ChatGPT Apps callers. If set, skip the script and share this URL with the user instead (see fallback section below).

### Step 2: Get the upload script

Call `skills_getScript`:

```json
{ "skillSlug": "upload-to-skillzdrive", "scriptName": "send-file.sh" }
```

### Step 3: Run the script locally

**IMPORTANT: must execute on the user's machine** (not in a sandbox — it needs filesystem access to read the file).

```bash
bash send-file.sh --file /path/to/the-skill.zip --upload-token ut_live_...
```

Substitute the real path and the `uploadToken` from Step 1.

Output on success:

```json
{
  "success": true,
  "skill": { "id": "uuid", "slug": "my-skill", "name": "My Skill" },
  "scriptsUploaded": 2,
  "filesUploaded": 1,
  "creditCost": 1,
  "collectionPlacement": { "status": "added" },
  "message": "Created skill 'My Skill' with 2 script(s) and 1 file(s)"
}
```

`collectionPlacement.status === 'added'` confirms the skill is in the target collection and will be visible to the current MCP session immediately.

## Can't run the script? Use the website fallback

If `websiteFallbackUrl` was returned in Step 1, or the local script can't execute (browser-based agents, sandboxed clients, ChatGPT Apps), share that URL with the user. They open it in their browser, drop in the file, and it's added to their drive (and collection if applicable). The ticket is unused in this path; no harm, it'll expire on its own.

## Platform Requirements

On platforms that restrict outbound domains for MCP servers, the user must whitelist `www.skillzdrive.com` for the script's POST to reach the server.

**Claude.ai:** [https://claude.ai/admin-settings/capabilities](https://claude.ai/admin-settings/capabilities) — add `www.skillzdrive.com` to allowed domains.

If whitelisting isn't available, use the website fallback URL instead.

## Important Notes

- **No embedded credentials.** The script accepts a ticket via `--upload-token`. Tickets are single-use and expire in 10 minutes. If an upload fails, mint a fresh one.
- **Supported formats:** `.zip` and `.skill` (which is also a zip).
- The zip must contain a `SKILL.md` with valid frontmatter (`name`, `description`, `tags`).
- Import credits are charged based on file size.
- If the user says "upload my skill" or "add this to my drive", this is the workflow to follow.
