# CoverableIssueResults

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/coverableissueresults.doc.html

*menu* Types OBJECT
 # CoverableIssueResults
 Coverable Issue Results type

## linkGraphQL Schema definition
 `1type CoverableIssueResults {23#   Total amount of issues.4total: Int 56#   The index of the first item to return in the page of results (page offset).7start: Int 89#   The maximum amount of Coverable Issues to be returned. The maximum is 100.10limit: Int 1112#   Test issue results.13results: [CoverableIssue] 1415#   Warnings generated if you have a invalid Coverable Issue16warnings: [String] 1718}`
## linkRequired by
 - ExpandedTestExpaded test issue typegetCoverableIssuesnullQuerynullTestTest issue type