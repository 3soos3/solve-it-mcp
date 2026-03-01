# NOTICE File Auto-Update Setup

This document explains how to enable full automation for NOTICE file updates, including automatic CI triggering and auto-merge.

## Current Behavior

The License Compliance workflow automatically:
1. ✅ Detects dependency changes
2. ✅ Generates updated NOTICE file
3. ✅ Creates a pull request
4. ⚠️ **Requires manual trigger for CI** (when using GITHUB_TOKEN)
5. ⚠️ **Requires manual merge**

## Full Automation Setup

To enable **automatic CI triggering and auto-merge**, set up a Personal Access Token (PAT):

### Option 1: Personal Access Token (Recommended)

1. **Create a PAT** (Classic or Fine-grained):
   - Go to: Settings → Developer settings → Personal access tokens
   - **Classic Token**: Select scopes: `repo`, `workflow`
   - **Fine-grained Token**: 
     - Repository access: Select this repository
     - Permissions: 
       - Contents: Read and write
       - Pull requests: Read and write
       - Workflows: Read and write

2. **Add secret to repository**:
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PAT`
   - Value: Your token
   - Click "Add secret"

3. **That's it!** Next NOTICE update will:
   - ✅ Automatically trigger CI checks
   - ✅ Auto-merge after CI passes
   - ✅ No manual intervention needed

### Option 2: GitHub App (Advanced)

For organization-level automation:

1. Create a GitHub App with permissions:
   - Contents: Read & write
   - Pull requests: Read & write
   - Workflows: Read & write

2. Install app on repository

3. Add app token as `BOT_TOKEN` secret

## How It Works

### Without PAT/BOT_TOKEN (Current)
```
Dependencies change → Generate NOTICE → Create PR → ⚠️ Manual: Trigger CI → ⚠️ Manual: Merge
```

### With PAT/BOT_TOKEN (Automated)
```
Dependencies change → Generate NOTICE → Create PR → ✅ Auto: CI runs → ✅ Auto: Merge
```

## Security Considerations

### Why GitHub Doesn't Auto-Trigger CI

GitHub Actions prevents workflows from triggering other workflows when using `GITHUB_TOKEN` to prevent:
- Infinite loops of workflows
- Unintended automation chains
- Resource exhaustion

### PAT Security Best Practices

1. **Use Fine-grained PAT** (more secure than Classic)
2. **Minimal permissions**: Only `Contents` and `Pull Requests`
3. **Repository-scoped**: Don't use personal PAT for org repos
4. **Rotate regularly**: Set expiration date
5. **Monitor usage**: Check GitHub audit log

## Testing

After setting up PAT, test the automation:

```bash
# Trigger the workflow manually
gh workflow run license-compliance.yml

# Or make a dependency change
echo "# test" >> requirements.txt
git add requirements.txt
git commit -m "test: trigger NOTICE update"
git push
```

Expected behavior:
1. Workflow creates PR
2. CI automatically runs on PR
3. After CI passes, PR auto-merges
4. No manual intervention needed

## Troubleshooting

### CI doesn't trigger on PR

**Symptom**: PR created but no CI checks show up

**Solution**: 
1. Verify PAT secret exists: Settings → Secrets → Actions → `PAT`
2. Check PAT permissions include `workflow` scope
3. Ensure PAT hasn't expired

### Auto-merge doesn't work

**Symptom**: PR created, CI passes, but doesn't auto-merge

**Solution**:
1. Enable auto-merge in repository: Settings → General → Pull Requests → Allow auto-merge
2. Verify PAT has `repo` scope
3. Check branch protection rules don't block auto-merge

### Permission errors

**Error**: `Resource not accessible by integration`

**Solution**: 
- PAT needs `workflow` scope (Classic) or `Workflows: Read & write` (Fine-grained)
- For fine-grained PAT, ensure repository access is granted

## Fallback Behavior

If PAT is not configured, workflow still works but requires manual steps:

1. PR is created automatically
2. You must manually trigger CI:
   - Close and reopen PR, OR
   - Push empty commit: `git commit --allow-empty -m 'trigger CI'`
3. Review and merge manually

## Additional Notes

- NOTICE updates only happen on `main` branch pushes
- Weekly check runs Sunday 1 AM UTC
- Changes only create PR if NOTICE content actually changed
- PR automatically labels: `automated`, `dependencies`

## Questions?

Check the workflow file: `.github/workflows/license-compliance.yml`
