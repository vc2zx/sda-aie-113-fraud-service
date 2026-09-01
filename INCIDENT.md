# Secret Exposure Incident Response

## Scenario

A repository scan identifies a credential committed to Git history.

## Response Order

1. Revoke or rotate the exposed credential immediately.
2. Determine where the credential was used and review access logs.
3. Remove the credential from the working tree.
4. Clean the credential from Git history when required.
5. Replace hard-coded credentials with environment-driven configuration.
6. Run secret scanning again and confirm the repository is clean.
7. Document the incident and prevention measures.

## Prevention

- Secrets must never be committed to Git.
- Secrets must never be baked into container images.
- Production secrets are injected through the runtime environment.
- Logs defensively mask sensitive keys.
- Secret scanning is performed before release.

## Lab 6 Drill

The training drill uses fake credentials only.
The response order remains: rotate first, investigate, clean, and prevent recurrence.
