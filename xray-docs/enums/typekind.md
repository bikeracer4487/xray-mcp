# __TypeKind

**Category:** Enums
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/typekind.spec.html

*menu* Types ENUM
 # __TypeKind
 An enum describing what kind of type a given__Typeis.

## linkGraphQL Schema definition
 `1enum __TypeKind {23#   Indicates this type is a scalar.4SCALAR56#   Indicates this type is an object. fields and interfaces are valid fields.7OBJECT89#   Indicates this type is an interface. fields and possibleTypes are valid fields.10INTERFACE1112#   Indicates this type is a union. possibleTypes is a valid field.13UNION1415#   Indicates this type is an enum. enumValues is a valid field.16ENUM1718#   Indicates this type is an input object. inputFields is a valid field.19INPUT_OBJECT2021#   Indicates this type is a list. ofType is a valid field.22LIST2324#   Indicates this type is a non-null. ofType is a valid field.25NON_NULL26}`
## linkRequired by
 - __TypeThe fundamental unit of any GraphQL Schema is the type. There are many kinds of types in GraphQL as represented by the `__TypeKind` enum.

Depending on the kind of a type, certain fields describe information about that type. Scalar types provide no information beyond a name and description, while Enum types provide their values. Object and Interface types provide the fields they describe. Abstract types, Union and Interface, provide the Object types possible at runtime. List and NonNull types compose other types.