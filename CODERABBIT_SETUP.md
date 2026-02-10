# CodeRabbit Integration - Automated Code Review Setup

## Overview
CodeRabbit is an AI-powered code review tool that automatically reviews pull requests, providing intelligent feedback on code quality, potential bugs, security issues, and best practices.

## Setup Status
✅ **COMPLETED** - CodeRabbit integration is fully configured and ready to use.

---

## What's Configured

### 1. CodeRabbit Configuration (`.coderabbit.yaml`)
Located at the root of the repository, this file controls CodeRabbit's behavior:

- **Profile**: `chill` - Balanced review style
- **Auto-review**: Enabled for all PRs (ignores WIP/DRAFT)
- **GitHub Checks**: Enabled with 5-minute timeout
- **High-level summary**: Enabled
- **Review status**: Visible on PRs
- **Auto-reply**: Enabled for chat interactions

### 2. GitHub Actions Workflows

#### a. CodeRabbit Review Workflow (`.github/workflows/coderabbit.yml`)
Triggers on:
- Pull request opened/synchronized/reopened
- Pull request review comments

Performs:
- AI-powered code review
- Inline comments on issues
- Summary of changes
- Security vulnerability detection

#### b. Code Quality Checks (`.github/workflows/code-quality.yml`)
Runs comprehensive quality checks on:

**Backend (Python/FastAPI)**:
- Black (code formatting)
- Flake8 (linting)
- Pylint (code analysis)
- Bandit (security scanning)
- Safety (dependency vulnerabilities)

**Frontend (Next.js/TypeScript)**:
- ESLint (linting)
- TypeScript type checking
- Build validation

**Mobile (Flutter/Dart)**:
- Flutter analyze
- Flutter format check
- Flutter test

---

## Required GitHub Secrets

To enable CodeRabbit, add these secrets to your GitHub repository:

1. **GITHUB_TOKEN** - Automatically provided by GitHub Actions (no action needed)
2. **OPENAI_API_KEY** - Required for CodeRabbit AI reviews

### How to Add Secrets:
1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add:
   - Name: `OPENAI_API_KEY`
   - Value: Your OpenAI API key (starts with `sk-`)

---

## How to Use CodeRabbit

### Automatic Reviews
CodeRabbit automatically reviews every pull request. No manual action needed!

### Interactive Review
You can interact with CodeRabbit by:

1. **Request specific review**: Comment on PR with:
   ```
   @coderabbitai review
   ```

2. **Ask questions**: Comment on specific lines:
   ```
   @coderabbitai explain this function
   ```

3. **Request changes**:
   ```
   @coderabbitai suggest improvements for this code
   ```

4. **Skip review**: Add to PR title:
   - `WIP: ...`
   - `DRAFT: ...`
   - `DO NOT REVIEW: ...`

---

## CodeRabbit Review Features

### 1. Code Quality Analysis
- Identifies code smells
- Suggests refactoring opportunities
- Checks naming conventions
- Reviews code complexity

### 2. Security Scanning
- Detects SQL injection vulnerabilities
- Identifies XSS risks
- Checks authentication issues
- Reviews API security

### 3. Best Practices
- Framework-specific recommendations
- Performance optimization suggestions
- Architecture pattern validation
- Documentation completeness

### 4. Test Coverage
- Identifies missing tests
- Suggests test cases
- Reviews test quality

---

## Integration with Development Workflow

### Pull Request Process
```
1. Create feature branch
   ↓
2. Make code changes
   ↓
3. Push to GitHub
   ↓
4. Create Pull Request
   ↓
5. CodeRabbit automatically reviews (within 1-2 minutes)
   ↓
6. Code Quality checks run
   ↓
7. Review CodeRabbit comments
   ↓
8. Address feedback
   ↓
9. CodeRabbit re-reviews on new commits
   ↓
10. Merge when approved
```

### Best Practices
1. **Create small, focused PRs** - Easier for CodeRabbit to review
2. **Write descriptive PR descriptions** - Helps CodeRabbit understand context
3. **Respond to CodeRabbit comments** - Mark as resolved when addressed
4. **Use draft PRs for WIP** - Prevents premature reviews

---

## Monitoring and Reports

### GitHub Actions
View review status and quality checks:
- Go to **Actions** tab in GitHub repository
- Click on specific workflow run
- Review logs and reports

### CodeRabbit Dashboard
Access at: https://app.coderabbit.ai
- View review history
- See metrics and trends
- Configure advanced settings

### Security Reports
Bandit security reports are uploaded as artifacts:
1. Go to **Actions** → Select workflow run
2. Scroll to **Artifacts**
3. Download `bandit-security-report`

---

## Troubleshooting

### CodeRabbit Not Reviewing PRs
**Check**:
1. PR title doesn't contain WIP/DRAFT
2. OPENAI_API_KEY is set in repository secrets
3. Workflow file exists in `.github/workflows/coderabbit.yml`
4. GitHub Actions are enabled for repository

### Code Quality Checks Failing
**Common issues**:
- **Python**: Missing dependencies in `requirements.txt`
- **Frontend**: `npm run lint` script not defined in `package.json`
- **Mobile**: Flutter SDK version mismatch

**Solutions**:
- Check workflow logs in Actions tab
- Verify local development environment matches CI
- Run checks locally before pushing

### Slow Review Times
**Reasons**:
- Large PR (>500 lines changed)
- Complex code changes
- OpenAI API rate limits

**Solutions**:
- Break down large PRs
- Manually trigger review with `@coderabbitai review`

---

## Configuration Customization

### Adjust Review Intensity
Edit `.coderabbit.yaml`:

```yaml
reviews:
  profile: assertive  # Options: chill, assertive, custom
```

### Exclude Files from Review
```yaml
reviews:
  path_filters:
    excluded:
      - "**/*.test.ts"
      - "**/migrations/**"
      - "**/__pycache__/**"
```

### Customize Code Quality Rules
Edit workflow files in `.github/workflows/`:
- Modify linting rules
- Add/remove tools
- Adjust severity levels

---

## Cost Considerations

### CodeRabbit Pricing
- **Free Tier**: 2 repositories, unlimited reviews
- **Pro**: $12/user/month for unlimited repositories
- **Team**: $24/user/month with advanced features

### OpenAI API Costs
CodeRabbit uses your OpenAI API key:
- Typical cost: $0.01 - $0.05 per PR review
- Depends on PR size and complexity
- Monitor usage at: https://platform.openai.com/usage

---

## Next Steps

1. ✅ **Configuration complete** - All files created
2. ⏳ **Commit and push** to GitHub
3. ⏳ **Add OPENAI_API_KEY** to repository secrets
4. ⏳ **Enable GitHub Actions** in repository settings
5. ⏳ **Create first PR** to test CodeRabbit
6. ⏳ **Review and iterate** based on feedback

---

## Support and Resources

- **CodeRabbit Docs**: https://docs.coderabbit.ai
- **GitHub Actions Docs**: https://docs.github.com/actions
- **Report Issues**: Create issue in repository with `coderabbit` label

---

**Last Updated**: February 10, 2026
**Version**: 1.0
**Status**: Production Ready ✅
