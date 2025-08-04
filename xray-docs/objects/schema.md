# __Schema

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/schema.spec.html

*menu* Types OBJECT
 # __Schema
 A GraphQL Schema defines the capabilities of a GraphQL server. It exposes all available types and directives on the server, as well as the entry points for query, mutation, and subscription operations.

## linkGraphQL Schema definition
 `1type __Schema {23#   A list of all types supported by this server.4types: [__Type!]! 56#   The type that query operations will be rooted at.7queryType: __Type! 89#   If this server supports mutation, the type that mutation operations will be rooted at.10mutationType: __Type 1112#   If this server support subscription, the type that subscription operations will be rooted at.13subscriptionType: __Type 1415#   A list of all directives supported by this server.16directives: [__Directive!]! 1718}`