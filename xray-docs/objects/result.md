# Result

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/result.doc.html

*menu* Types OBJECT
 # Result
 Result Type

## linkGraphQL Schema definition
 `1type Result {23#   Output if exist an error or a failure (JUNIT, XUNIT, NUNIT, TESTNG)4log: String 56#   Examples of the Result.7examples: [ResultsExample] 89#   Whether or not the Result was imported.10wasImported: String 1112#   Duration of the Result.13duration: Float 1415#   Status of the Result.16status: StepStatus 1718#   Name of the Result.19name: String 2021#   Hooks of the Results.22hooks: [ResultsStep] 2324#   Backgrounds of the Results.25backgrounds: [ResultsStep] 2627#   Steps of the Results.28steps: [ResultsStep] 2930}`
## linkRequired by
 - TestRunTest Run type