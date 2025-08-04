# __Directive

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/directive.spec.html

*menu* Types OBJECT
 # __Directive
 A Directive provides a way to describe alternate runtime execution and type validation behavior in a GraphQL document.
 In some cases, you need to provide options to alter GraphQL's execution behavior in ways field arguments will not suffice, such as conditionally including or skipping a field. Directives provide this by describing additional information to the executor.

## linkGraphQL Schema definition
 `1type __Directive {23name: String! 45description: String 67locations: [__DirectiveLocation!]! 89args: [__InputValue!]! 1011}`
## linkRequired by
 - __SchemaA GraphQL Schema defines the capabilities of a GraphQL server. It exposes all available types and directives on the server, as well as the entry points for query, mutation, and subscription operations.