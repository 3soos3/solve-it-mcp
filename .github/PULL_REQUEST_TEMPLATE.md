# Pull Request

## Description

<!-- Describe your changes in detail -->

## Type of Change

- [ ] 🐛 Bug fix (patch version bump)
- [ ] ✨ New feature (minor version bump)
- [ ] 💥 Breaking change (major version bump)
- [ ] 🔒 Security fix (requires "security" label for full scan)
- [ ] 📚 Documentation update
- [ ] 🔧 Build/CI changes
- [ ] ♻️ Code refactoring

## Security Scanning

This PR will trigger:

- **Draft PR**: Quick scan (AMD64 only, ~10 min)
- **Ready for Review**: Full scan (AMD64, ARM64, ARM/v7, ~22 min)
- **"security" label**: Full scan even in draft mode

**Mark as draft** for fast feedback during development.
**Mark ready for review** when complete for comprehensive validation.

## Testing

<!-- Describe the tests you ran -->

- [ ] Local testing completed
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Multi-architecture build tested (if applicable)
- [ ] Security scan passed (will be verified by CI)

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings or errors
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Version Impact

<!-- Will this require a version bump? -->

**Current version**: (check latest tag)
**Proposed version**: (if applicable)

**SOLVE-IT version**: (check if updated)

## Additional Context

<!-- Add any other context about the PR here -->
<!-- Screenshots, logs, benchmarks, etc. -->

---

**For Maintainers:**

- Add **"security"** label if this PR contains security-sensitive changes
- Ensure all 3 platform scans pass before merging
- Update CHANGELOG before merge (if applicable)
- Consider creating a release after merge (if applicable)
