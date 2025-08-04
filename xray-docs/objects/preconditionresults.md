# PreconditionResults

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/preconditionresults.doc.html

*menu* Types OBJECT
 # PreconditionResults
 Precondition Results type

## linkGraphQL Schema definition
 `1type PreconditionResults {23#   Total amount of issues.4total: Int 56#   Index of the first item to return in the page of results (page offset).7start: Int 89#   Maximum amount of Preconditions to be returned. The maximum is 100.10limit: Int 1112#   Precondition issue results.13results: [Precondition] 1415}`
## linkRequired by
 - ExpandedTestExpaded test issue typegetPreconditionsnullQuerynullTestTest issue typeTestVersionnull