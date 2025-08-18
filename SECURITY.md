# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Yes             |

## Reporting a Vulnerability

**DO NOT** open public GitHub issues for security vulnerabilities.

### For Security Issues:
1. **Email**: Send details to the repository maintainer via GitHub's private vulnerability reporting
2. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### Response Timeline:
- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Status Update**: Weekly during investigation
- **Resolution**: Target 30 days for critical issues

### Security Update Policy:
- Critical vulnerabilities: Immediate patch release
- High severity: Patch within 1 week
- Medium/Low severity: Next scheduled release

### Disclosure Policy:
We follow coordinated disclosure. We'll work with you to understand and resolve 
the issue before any public disclosure.

### Security Considerations

This MCP server handles sensitive authentication credentials:
- **Xray API credentials** (Client ID and Secret)
- **JWT tokens** with API access

**Important Security Notes:**
- Never commit real API credentials to version control
- Use environment variables for all sensitive configuration
- Regularly rotate API credentials
- Monitor for unauthorized API usage
- Keep dependencies updated for security patches

### Known Security Limitations

- This server requires network access to Xray Cloud/Server instances
- JWT tokens are cached in memory during server operation
- GraphQL queries may expose project structure information