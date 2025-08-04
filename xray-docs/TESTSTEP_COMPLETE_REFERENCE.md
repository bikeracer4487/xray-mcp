# TestStep Complete Reference

This document consolidates all TestStep-related operations, objects, and types from the XRAY GraphQL API.

## Table of Contents

1. [Queries](#queries)
   - [getStepStatus](#getstepstatus)
   - [getStepStatuses](#getstepstatuses)
2. [Mutations](#mutations)
   - [addTestStep](#addteststep)
   - [updateTestStep](#updateteststep)
   - [removeTestStep](#removeteststep)
   - [removeAllTestSteps](#removeallteststeps)
3. [Objects](#objects)
   - [CustomStepField](#customstepfield)
   - [ExpandedStep](#expandedstep)
   - [ProjectSettingsTestStepField](#projectsettingsteststepfield)
   - [ProjectSettingsTestStepSettings](#projectsettingsteststepsettings)
   - [ResultsStep](#resultsstep)
   - [Step](#step)
   - [StepStatus](#stepstatus)
   - [UpdateTestStepResult](#updateteststepresult)
4. [Input Objects](#input-objects)
   - [CreateStepInput](#createstepinput)
   - [CustomStepFieldInput](#customstepfieldinput)
   - [UpdateStepInput](#updatestepinput)

---

## Queries

### getStepStatus

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getstepstatus.doc.html

Returns a Step Status by name.

```graphql
{
    getStepStatus( name: "PASSED") {
        name
        description
        color
    }
}
```

### getStepStatuses

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getstepstatuses.doc.html

Returns all available Step Statuses.

```graphql
{
    getStepStatuses {
        name
        description
        color
    }
}
```

---

## Mutations

### addTestStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addteststep.doc.html

Adds a new Step to a Test.

```graphql
mutation {
    addTestStep(
        issueId: "12345",
        step: {
            action: "Use Xray Cloud Rest Api to add a new Step to the Test",
            result: "Step was added to the Test",
            customFields: [{id:"5ddc0e585da9670010e608dc", value:"Tokyo"}]
        }
    ) {
        id
        action
        data
        result
    }
}
```

**Adding a step to a specific version:**
```graphql
mutation {
    addTestStep(
        issueId: "12345",
        versionId: 3,
        step: {
            action: "Use Xray Cloud Rest Api to add a new Step to the Test",
            result: "Step was added to the Test",
            customFields: [{id:"5ddc0e585da9670010e608dc", value:"Tokyo"}]
        }
    ) {
        id
        action
        data
        result
    }
}
```

### updateTestStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updateteststep.doc.html

Updates an existing Test Step.

```graphql
mutation {
    updateTestStep(
        stepId: "836d30ec-f034-4a03-879e-9c44a1d6d1fe",
        step: {
            result: "Xray Cloud Rest Api works as expected",
            customFields: [{id:"5ddc0e585da9670010e608dc", value:"Lisbon"}]
        }
    ) {
        warnings
    }
}
```

### removeTestStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removeteststep.doc.html

Removes a Test Step by its ID.

```graphql
mutation {
    removeTestStep(
        stepId: "836d30ec-f034-4a03-879e-9c44a1d6d1fe",
    )
}
```

### removeAllTestSteps

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removeallteststeps.doc.html

Removes all Steps from a Test.

```graphql
mutation {
    removeAllTestSteps(
        issueId: "12345",
    )
}
```

**Removing all steps from a specific version:**
```graphql
mutation {
    removeAllTestSteps(
        issueId: "12345",
        versionId: 3
    )
}
```

---

## Objects

### CustomStepField

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/customstepfield.doc.html

Step CustomField type.

```graphql
type CustomStepField {
    # Id of the Custom Field.
    id: String 
    
    # Name of the Custom Field.
    name: String 
    
    # Value of the Custom Field.
    value: JSON 
}
```

### ExpandedStep

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/expandedstep.doc.html

Expanded test step type with additional relationship information.

```graphql
type ExpandedStep {
    # Id of the Step.
    id: String 
    
    # Action of the Step.
    action: String 
    
    # Data of the Step.
    data: String 
    
    # Result of the Step.
    result: String 
    
    # Attachments of the Step.
    attachments: [Attachment] 
    
    # Custom Fields of the Step.
    customFields: [CustomStepField] 
    
    # The issue id of the called test with the step
    calledTestIssueId: String 
    
    # The issue id of the test calling the step
    parentTestIssueId: String 
}
```

### ProjectSettingsTestStepField

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/projectsettingsteststepfield.doc.html

Project Test Step Field Settings type.

```graphql
type ProjectSettingsTestStepField {
    # Id
    id: String 
    
    # Name
    name: String 
    
    # Type
    type: String 
    
    # Is the field required
    required: Boolean 
    
    # Is the field disabled
    disabled: Boolean 
    
    # Values
    values: [String] 
}
```

### ProjectSettingsTestStepSettings

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/projectsettingsteststepsettings.doc.html

Project Test Step Settings type.

```graphql
type ProjectSettingsTestStepSettings {
    # Fields
    fields: [ProjectSettingsTestStepField] 
}
```

### ResultsStep

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/resultsstep.doc.html

Results Step type - used in test execution results.

```graphql
type ResultsStep {
    # If a gherkin step, keyword of the gherkin step.
    keyword: String 
    
    # Name of the step.
    name: String 
    
    # Embeddings of the step.
    embeddings: [ResultsEmbedding] 
    
    # Duration of the step.
    duration: Float 
    
    # Error of the step.
    error: String 
    
    # Status of the step.
    status: StepStatus 
    
    # If a Robot step, output of the Robot step.
    log: String 
}
```

### Step

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/step.doc.html

Test Step type.

```graphql
type Step {
    # Id of the Step.
    id: String 
    
    # Action of the Step.
    action: String 
    
    # Data of the Step.
    data: String 
    
    # Result of the Step.
    result: String 
    
    # Attachments of the Step.
    attachments: [Attachment] 
    
    # Custom Fields of the Step.
    customFields: [CustomStepField] 
    
    # The issue id of the test being called in the step.
    callTestIssueId: String 
}
```

### StepStatus

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/stepstatus.doc.html

Step Status type. Referenced by various step-related objects including ResultsStep, TestRunIteration, TestRunIterationStepResult, and TestRunStep.

### UpdateTestStepResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updateteststepresult.doc.html

Update Test Step Results type.

```graphql
type UpdateTestStepResult {
    # List of added attachments.
    addedAttachments: [String] 
    
    # List of removed attachments.
    removedAttachments: [String] 
    
    # Warnings generated during the operation.
    warnings: [String] 
}
```

---

## Input Objects

### CreateStepInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/createstepinput.doc.html

Create Step input type.

```graphql
input CreateStepInput {
    # Action of the Step.
    action: String
    
    # Data of the Step.
    data: String
    
    # Result of the Step.
    result: String
    
    # Attachments of the Step.
    attachments: [AttachmentInput]
    
    # Custom Fields of the Step
    customFields: [CustomStepFieldInput]
    
    # The issue id of the test called by the step.
    callTestIssueId: String
}
```

### CustomStepFieldInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/customstepfieldinput.doc.html

Step Custom Field input type.

```graphql
input CustomStepFieldInput {
    # Id of the Custom Field.
    id: String
    
    # value of the Custom Field.
    value: JSON
}
```

### UpdateStepInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatestepinput.doc.html

Update Step input type.

```graphql
input UpdateStepInput {
    # Action of the Step.
    action: String
    
    # Data of the Step.
    data: String
    
    # Result of the Step.
    result: String
    
    # Attachments of the Step.
    attachments: AttachmentOperationsInput
    
    # Custom Fields of the Step
    customFields: [CustomStepFieldInput]
}
```