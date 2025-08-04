# XrayHistoryEntry

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/xrayhistoryentry.doc.html

*menu* Types OBJECT
 # XrayHistoryEntry
 Xray History Entry type

## linkGraphQL Schema definition
 `1type XrayHistoryEntry {23#   Test Version that the changes refer to (if applicable).4version: String 56#   User that performed the change(s).7user: String 89#   Date of change(s).10date: String 1112#   Action performed.13action: String 1415#   Details of the change(s).16changes: [Changes] 1718}`
## linkRequired by
 - XrayHistoryResultsXray History Results type