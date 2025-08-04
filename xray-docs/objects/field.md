# __Field

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/field.spec.html

*menu* Types OBJECT
 # __Field
 Object and Interface types are described by a list of Fields, each of which has a name, potentially a list of arguments, and a return type.

## linkGraphQL Schema definition
 `1type __Field {23name: String! 45description: String 67args: [__InputValue!]! 89type: __Type! 1011isDeprecated: Boolean! 1213deprecationReason: String 1415}`
## linkRequired by
 - __TypeThe fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the `__TypeKind` enum.

Depending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.