# CoverableIssue

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/coverableissue.doc.html

*menu* Types OBJECT
 # CoverableIssue

## linkGraphQL Schema definition
 `1type CoverableIssue {23issueId: String 45# Arguments6#   issueIds: [Not documented]7#   limit: [Not documented]8#   start: [Not documented]9tests(issueIds: [String], limit: Int!, start: Int): TestResults 1011# Arguments12#   fields: [Not documented]13jira(fields: [String]): JSON! 1415# Arguments16#   environment: [Not documented]17#   isFinal: [Not documented]18#   version: [Not documented]19#   testPlan: [Not documented]20status(environment: String, isFinal: Boolean, version: String, testPlan: String): CoverageStatus 2122}`
## linkRequired by
 - CoverableIssueResultsCoverable Issue Results typegetCoverableIssuenullQuerynull