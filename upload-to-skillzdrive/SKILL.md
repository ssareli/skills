---
name: upload-to-skillzdrive
description: Upload a local .zip or .skill file to your SkillzDrive. Includes a bash script that must be run locally to upload and create the skill in one step.
tags: [utility, upload, skillzdrive, file-transfer]
execution_tier: local
---

# Upload to SkillzDrive

This skill uploads a local `.zip` or `.skill` file from the user's machine to their SkillzDrive. The script handles everything in one step: uploading the file, parsing the ZIP, creating the skill, and adding it to the user's drive.

## Step-by-Step Workflow

### Step 1: Get the upload script

Call the `skills_getScript` MCP tool:
```json
{
  "skillSlug": "upload-to-skillzdrive",
  "scriptName": "send-file.sh"
}
```

This returns a bash script with an embedded upload API key unique to the user.

### Step 2: Run the script LOCALLY

**IMPORTANT: This script MUST be executed on the user's local machine.** It cannot be run in a sandbox or remote environment — it needs access to the local filesystem to read the file being uploaded.

Save the script content to a temporary file and execute it:

```bash
bash send-file.sh --file /path/to/the-skill.zip
```

Replace `/path/to/the-skill.zip` with the actual path to the user's `.zip` or `.skill` file.

The script will upload and process the file in one step. The output JSON contains the created skill info:
```json
{
  "success": true,
  "skill": { "id": "uuid", "slug": "my-skill", "name": "My Skill" },
  "scriptsUploaded": 2,
  "filesUploaded": 1,
  "creditCost": 1,
  "message": "Created skill 'My Skill' with 2 script(s) and 1 file(s)"
}
```

That's it! The skill is now in the user's drive and ready to use.

## Important Notes

- The `send-file.sh` script contains the user's upload-only API key. This key can ONLY upload files — it cannot be used for MCP connections.
- Supported file formats: `.zip` and `.skill` (which is also a zip).
- The zip must contain a `SKILL.md` file with valid frontmatter (name, description, tags).
- Import credits are charged based on file size.
- If the user says "upload my skill" or "add this to my drive", this is the workflow to follow.