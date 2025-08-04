# __Type

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/type.spec.html

*menu* Types OBJECT
 # __Type
 The fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the__TypeKindenum.
 Depending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.

## linkGraphQL Schema definition
 `1type __Type {23kind: __TypeKind! 45name: String 67description: String 89# Arguments10#   includeDeprecated: [Not documented]11fields(includeDeprecated: Boolean): [__Field!] 1213interfaces: [__Type!] 1415possibleTypes: [__Type!] 1617# Arguments18#   includeDeprecated: [Not documented]19enumValues(includeDeprecated: Boolean): [__EnumValue!] 2021inputFields: [__InputValue!] 2223ofType: __Type 2425}`
## linkRequired by
 - __FieldObject and Interface types are described by a list of Fields, each of which has a name, potentially a list of arguments, and a return type.__InputValueArguments provided to Fields or Directives and the input fields of an InputObject are represented as Input Values which describe their type and optionally a default value.__SchemaA GraphQL Schema defines the capabilities of a GraphQL server. It exposes all available types and directives on the server, as well as the entry points for query, mutation, and subscription operations.__TypeThe fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the `__TypeKind` enum.

Depending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.