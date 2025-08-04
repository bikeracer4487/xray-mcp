# XrayHistoryResults

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/xrayhistoryresults.doc.html

*menu* Types OBJECT
 # XrayHistoryResults
 Xray History Results type

## linkGraphQL Schema definition
 `1type XrayHistoryResults {23#   Total amount of issues.4total: Int 56#   Index of the first item to return in the page of results (page offset).7start: Int 89#   Maximum amount of History results to be returned. The maximum is 100.10limit: Int 1112#   Precondition issue results.13results: [XrayHistoryEntry] 1415}`
## linkRequired by
 - ExpandedTestExpaded test issue typePreconditionPrecondition issue typeTestTest issue typeTestExecutionTest Execution issue typeTestPlanTest Plan issue typeTestSetTest Set type