# __InputValue

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/inputvalue.spec.html

*menu* Types OBJECT
 # __InputValue
 Arguments provided to Fields or Directives and the input fields of an InputObject are represented as Input Values which describe their type and optionally a default value.

## linkGraphQL Schema definition
 `1type __InputValue {23name: String! 45description: String 67type: __Type! 89#   A GraphQL-formatted string representing the default value for this input value.10defaultValue: String 1112}`
## linkRequired by
 - __DirectiveA Directive provides a way to describe alternate runtime execution and type validation behavior in a GraphQL document.

In some cases, you need to provide options to alter GraphQL's execution behavior in ways field arguments will not suffice, such as conditionally including or skipping a field. Directives provide this by describing additional information to the executor.__FieldObject and Interface types are described by a list of Fields, each of which has a name, potentially a list of arguments, and a return type.__TypeThe fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the `__TypeKind` enum.

Depending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.