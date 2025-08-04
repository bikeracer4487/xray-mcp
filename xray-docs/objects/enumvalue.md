# __EnumValue

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/enumvalue.spec.html

*menu* Types OBJECT
 # __EnumValue
 One possible value for a given Enum. Enum values are unique values, not a placeholder for a string or numeric value. However an Enum value is returned in a JSON response as a string.

## linkGraphQL Schema definition
 `1type __EnumValue {23name: String! 45description: String 67isDeprecated: Boolean! 89deprecationReason: String 1011}`
## linkRequired by
 - __TypeThe fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the `__TypeKind` enum.

Depending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.