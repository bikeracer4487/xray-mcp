# __DirectiveLocation

**Category:** Enums
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/directivelocation.spec.html

*menu* Types ENUM
 # __DirectiveLocation
 A Directive can be adjacent to many parts of the GraphQL language, a __DirectiveLocation describes one such possible adjacencies.

## linkGraphQL Schema definition
 `1enum __DirectiveLocation {23#   Location adjacent to a query operation.4QUERY56#   Location adjacent to a mutation operation.7MUTATION89#   Location adjacent to a subscription operation.10SUBSCRIPTION1112#   Location adjacent to a field.13FIELD1415#   Location adjacent to a fragment definition.16FRAGMENT_DEFINITION1718#   Location adjacent to a fragment spread.19FRAGMENT_SPREAD2021#   Location adjacent to an inline fragment.22INLINE_FRAGMENT2324#   Location adjacent to a variable definition.25VARIABLE_DEFINITION2627#   Location adjacent to a schema definition.28SCHEMA2930#   Location adjacent to a scalar definition.31SCALAR3233#   Location adjacent to an object type definition.34OBJECT3536#   Location adjacent to a field definition.37FIELD_DEFINITION3839#   Location adjacent to an argument definition.40ARGUMENT_DEFINITION4142#   Location adjacent to an interface definition.43INTERFACE4445#   Location adjacent to a union definition.46UNION4748#   Location adjacent to an enum definition.49ENUM5051#   Location adjacent to an enum value definition.52ENUM_VALUE5354#   Location adjacent to an input object type definition.55INPUT_OBJECT5657#   Location adjacent to an input object field definition.58INPUT_FIELD_DEFINITION59}`
## linkRequired by
 - __DirectiveA Directive provides a way to describe alternate runtime execution and type validation behavior in a GraphQL document.

In some cases, you need to provide options to alter GraphQL's execution behavior in ways field arguments will not suffice, such as conditionally including or skipping a field. Directives provide this by describing additional information to the executor.