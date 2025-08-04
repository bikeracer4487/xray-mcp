# ProjectSettings

**Category:** Objects
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/projectsettings.doc.html

*menu* Types OBJECT
 # ProjectSettings
 Project Settings type

## linkGraphQL Schema definition
 `1type ProjectSettings {23#   Project id.4projectId: String 56#   Test Environments.7testEnvironments: [String] 89#   Test Coverage Settings.10testCoverageSettings: ProjectSettingsTestCoverage 1112#   Defect Issue Types.13defectIssueTypes: [String] 1415#   Test Type Settings.16testTypeSettings: ProjectSettingsTestType 1718#   Test Step Settings.19testStepSettings: ProjectSettingsTestStepSettings 2021#   Test Run Custom Fields Settings.22testRunCustomFieldSettings: ProjectSettingsTestRunCustomFields 2324}`
## linkRequired by
 - getProjectSettingsnullQuerynull