# Parameter

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/parameter.doc.html

*menu* Types OBJECT
 # Parameter
 Parameter type
Represents a single parameter in the Dataset.

## linkGraphQL Schema definition
 `1type Parameter {23#   The name of the parameter.4name: String 56#   The type of the parameter.7type: String 89#   The ID of the project list associated with the parameter.10projectListId: String 1112#   Indicates whether the parameter supports combinations.13combinations: Boolean 1415#   The list of values for the parameter.16listValues: [String] 1718}`
## linkRequired by
 - DatasetDataset type
Represents a single Dataset entity with its metadata, parameters, and associated dataset rows.