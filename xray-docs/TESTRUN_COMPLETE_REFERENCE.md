# TestRun Complete Reference

This document consolidates all TestRun-related operations, objects, and types from the XRAY GraphQL API.

## Table of Contents

1. [Queries](#queries)
   - [getTestRun](#gettestrun)
   - [getTestRunById](#gettestrunbyid)
   - [getTestRuns](#gettestruns)
   - [getTestRunsById](#gettestrunsbyid)
2. [Mutations](#mutations)
   - [resetTestRun](#resettestrun)
   - [updateTestRunStatus](#updatetestrunstatus)
   - [updateTestRunComment](#updatetestruncomment)
   - [updateTestRun](#updatetestrun)
   - [addDefectsToTestRun](#adddefectstotestrun)
   - [removeDefectsFromTestRun](#removedefectsfromtestrun)
   - [addEvidenceToTestRun](#addevidencetotestrun)
   - [removeEvidenceFromTestRun](#removeevidencefromtestrun)
   - [updateTestRunStep](#updatetestrunstep)
   - [addEvidenceToTestRunStep](#addevidencetotestrunstep)
   - [removeEvidenceFromTestRunStep](#removeevidencefromtestrunstep)
   - [addDefectsToTestRunStep](#adddefectstotestrunstep)
   - [removeDefectsFromTestRunStep](#removedefectsfromtestrunstep)
   - [updateTestRunStepComment](#updatetestrunstepcomment)
   - [updateTestRunStepStatus](#updatetestrunstepstatus)
   - [updateTestRunExampleStatus](#updatetestrunexamplestatus)
   - [setTestRunTimer](#settestruntimer)
3. [Objects](#objects)
   - [TestRun](#testrun-object)
   - [ProjectSettingsTestRunCustomField](#projectsettingstestruncustomfield)
   - [ProjectSettingsTestRunCustomFields](#projectsettingstestruncustomfields)
   - [TestRunCustomFieldValue](#testruncustomfieldvalue)
   - [TestRunCustomStepField](#testruncustomstepfield)
   - [TestRunIteration](#testruniteration)
   - [TestRunIterationResults](#testruniterationresults)
   - [TestRunIterationStepResult](#testruniterationstepresult)
   - [TestRunIterationStepResults](#testruniterationstepresults)
   - [TestRunParameter](#testrunparameter)
   - [TestRunPrecondition](#testrunprecondition)
   - [TestRunPreconditionResults](#testrunpreconditionresults)
   - [TestRunResults](#testrunresults)
   - [TestRunStep](#testrunstep)
   - [UpdateTestRunExampleStatusResult](#updatetestrunexamplestatusresult)
   - [UpdateTestRunResult](#updatetestrunresult)
   - [UpdateTestRunStepResult](#updatetestrunstepresult)
   - [UpdateTestRunStepStatusResult](#updatetestrunstepstatusresult)
4. [Input Objects](#input-objects)
   - [TestRunDefectOperationsInput](#testrundefectoperationsinput)
   - [TestRunEvidenceOperationsInput](#testrunevidenceoperationsinput)
   - [UpdateTestRunStepInput](#updatetestrunstepinput)

---

## Queries

### getTestRun

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestrun.doc.html

Returns a Test Run based on Test Issue ID and Test Execution Issue ID.

```graphql
{
    getTestRun( testIssueId: "11165", testExecIssueId: "11164") {
        id
        status {
            name
            color
            description
        }
        gherkin
        examples {
            id
            status {
                name
                color
                description
            }
        }
    }
}
```

### getTestRunById

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestrunbyid.doc.html

Returns a Test Run by its ID.

```graphql
{
    getTestRunById( id: "5acc7ab0a3fe1b6fcdc3c737") {
        id
        status {
            name
            color
            description
        }
        steps {
            action
            data
            result
            attachments {
                id
                filename
            }
            status {
                name
                color
            }
        }
    }
}
```

### getTestRuns

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestruns.doc.html

Returns Test Runs matching the given test issue IDs and test execution issue IDs.

```graphql
{
    getTestRuns( testIssueIds: ["10001", "10002"], testExecIssueIds: ["10001", "10002"], limit: 100 ) {
        total
        limit
        start
        results {
            id
            status {
                name
                color
                description
            }
            gherkin
            examples {
                id
                status {
                name
                color
                description
                }
            }
            test {
                issueId
            }
            testExecution {
                issueId
            }
        }
    }
}
```

**Example with steps:**
```graphql
{
    getTestRuns( testIssueIds: ["12345"], limit: 100 ) {
        total
        limit
        start
        results {
            id
            status {
                name
                color
                description
            }
            steps {
                action
                data
                result
                attachments {
                    id
                    filename
                }
                status {
                    name
                    color
                }
            }
            test {
                issueId
            }
            testExecution {
                issueId
            }
        }
    }
}
```

### getTestRunsById

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/gettestrunsbyid.doc.html

Returns Test Runs matching the given IDs.

```graphql
{
    getTestRunsById( ids: ["5acc7ab0a3fe1b6fcdc3c737"], limit: 10 ) {
        total
        limit
        start
        results {
            id
            status {
                name
                color
                description
            }
            gherkin
            examples {
                id
                status {
                    name
                    color
                    description
                }
            }
            test {
                issueId
            }
            testExecution {
                issueId
            }
        }
    }
}
```

---

## Mutations

### resetTestRun

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/resettestrun.doc.html

Resets a Test Run.

```graphql
mutation {
    resetTestRun( id: "5acc7ab0a3fe1b6fcdc3c737")
}
```

### updateTestRunStatus

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunstatus.doc.html

Updates the status of a Test Run.

```graphql
mutation {
    updateTestRunStatus( id: "5acc7ab0a3fe1b6fcdc3c737", status: "PASSED")
}
```

### updateTestRunComment

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestruncomment.doc.html

Updates the comment of a Test Run.

```graphql
mutation {
    updateTestRunComment( id: "5acc7ab0a3fe1b6fcdc3c737", comment: "Everything is OK.")
}
```

### updateTestRun

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrun.doc.html

Updates multiple fields of a Test Run.

```graphql
mutation {
    updateTestRun( id: "5acc7ab0a3fe1b6fcdc3c737", comment: "Everything is OK.", startedOn: "2020-03-09T10:35:09Z", finishedOn: "2020-04-09T10:35:09Z", assigneeId: "e5983db2-90f7-4135-a96f-46907e72290e", executedById: "e5983db2-90f7-4135-a96f-46907e72290e") {
        warnings
    }
}
```

### addDefectsToTestRun

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/adddefectstotestrun.doc.html

Adds defects to a Test Run.

```graphql
mutation {
    addDefectsToTestRun( id: "5acc7ab0a3fe1b6fcdc3c737", issues: ["XRAY-1234", "12345"]) {
        addedDefects
        warnings
    }
}
```

### removeDefectsFromTestRun

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removedefectsfromtestrun.doc.html

Removes defects from a Test Run.

```graphql
mutation {
    removeDefectsFromTestRun( id: "5acc7ab0a3fe1b6fcdc3c737", issues: ["XRAY-1234", "12345"])
}
```

### addEvidenceToTestRun

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addevidencetotestrun.doc.html

Adds evidence to a Test Run.

```graphql
mutation {
    addEvidenceToTestRun(
        id: "5acc7ab0a3fe1b6fcdc3c737",
        evidence: [
            {
                filename: "evidence.txt"
                mimeType: "text/plain"
                data: "SGVsbG8gV29ybGQ="
            }
        ]
    ) {
        addedEvidence
        warnings
    }
}
```

### removeEvidenceFromTestRun

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removeevidencefromtestrun.doc.html

Removes evidence from a Test Run.

```graphql
mutation {
    removeEvidenceFromTestRun(
        id: "5acc7ab0a3fe1b6fcdc3c737",
        evidenceFilenames: ["evidence.txt"]
    ) {
        removedEvidence
        warnings
    }
}
```

### updateTestRunStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunstep.doc.html

Updates a Test Run Step including status, comment, and defects.

```graphql
mutation {
    updateTestRunStep(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        stepId: "316eb258-10bb-40c0-ae40-ab76004cc505",
        updateData: {
            comment: "Step failed"
            status: "FAILED"
            defects: {
                add: ["12345"]
            }
        }
    ) {
        addedDefects
        warnings
    }
}
```

### addEvidenceToTestRunStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/addevidencetotestrunstep.doc.html

Adds evidence to a Test Run Step.

```graphql
mutation {
    addEvidenceToTestRunStep(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        stepId: "316eb258-10bb-40c0-ae40-ab76004cc505",
        evidence: [
            {
                filename: "evidence.txt"
                mimeType: "text/plain"
                data: "SGVsbG8gV29ybGQ="
            }
        ]
    ) {
        addedEvidence
        warnings
    }
}
```

### removeEvidenceFromTestRunStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removeevidencefromtestrunstep.doc.html

Removes evidence from a Test Run Step.

```graphql
mutation {
    removeEvidenceFromTestRunStep(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        stepId: "316eb258-10bb-40c0-ae40-ab76004cc505",
        evidenceFilenames: ["evidence.txt"]
    ) {
        removedEvidence
        warnings
    }
}
```

### addDefectsToTestRunStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/adddefectstotestrunstep.doc.html

Adds defects to a Test Run Step.

```graphql
mutation {
    addDefectsToTestRunStep(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        stepId: "316eb258-10bb-40c0-ae40-ab76004cc505",
        issues: ["XRAY-1234", "12345"]
    ) {
        addedDefects
        warnings
    }
}
```

### removeDefectsFromTestRunStep

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/removedefectsfromtestrunstep.doc.html

Removes defects from a Test Run Step.

```graphql
mutation {
    removeDefectsFromTestRunStep(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        stepId: "316eb258-10bb-40c0-ae40-ab76004cc505",
        issues: ["XRAY-1234", "12345"]
    ) {
        removedDefects
        warnings
    }
}
```

### updateTestRunStepComment

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunstepcomment.doc.html

Updates the comment of a Test Run Step.

```graphql
mutation {
    updateTestRunStepComment(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        stepId: "316eb258-10bb-40c0-ae40-ab76004cc505",
        comment: "This step is OK."
    )
}
```

### updateTestRunStepStatus

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunstepstatus.doc.html

Updates the status of a Test Run Step.

```graphql
mutation {
    updateTestRunStepStatus(
        testRunId: "5e8489c05f200f3cd45bbaf0",
        stepId: "316eb258-10bb-40c0-ae40-ab76004cc505",
        status: "PASSED"
    ) {
        warnings
    }
}
```

### updateTestRunExampleStatus

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunexamplestatus.doc.html

Updates the status of a Test Run Example.

```graphql
mutation {
    updateTestRunExampleStatus(
        exampleId: "5bbd8ab0a3fe1b6fcdc3c737",
        status: "PASSED"
    ) {
        warnings
    }
}
```

### setTestRunTimer

**Category:** Mutations  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/settestruntimer.doc.html

Starts or stops the timer in a Test Run.

**Start timer:**
```graphql
mutation {
    setTestRunTimer( 
        testRunId: "5acc7ab0a3fe1b6fcdc3c737"
        running: true
    ) {
        warnings
    }
}
```

**Stop timer:**
```graphql
mutation {
    setTestRunTimer( 
        testRunId: "5acc7ab0a3fe1b6fcdc3c737"
        reset: true
    ) {
        warnings
    }
}
```

---

## Objects

### TestRun Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrun.doc.html

Test Run type definition.

```graphql
type TestRun {
    # Id of the Test Run.
    id: String 
    
    # Status of the Test Run.
    status: Status 
    
    # Generic definition of the Test issue.
    unstructured: String 
    
    # Cucumber definition of the Test issue.
    gherkin: String 
    
    # Cucumber Type definition of the Test Run.
    scenarioType: String 
    
    # Comment definition of the Test Run.
    comment: String 
    
    # Started On date of the Test Run.
    startedOn: String 
    
    # Evidence of the Test Run.
    evidence: [Evidence] 
    
    # Defects of the Test Run.
    defects: [String] 
    
    # Step definition of the Test Run.
    steps: [TestRunStep] 
    
    # Examples of the Test Run.
    examples: [Example] 
    
    # Results of the Test Run.
    results: [Result] 
    
    # Test Type of the Test Run.
    testType: TestType 
    
    # User's account id that executed the Test Run.
    executedById: String 
    
    # User's account id assigned to the Test Run. This is user assigned to the Test Run, not taking into account the assignee of the test execution.
    assigneeId: String 
    
    # Finished On date of the Test Run.
    finishedOn: String 
    
    # Preconditions of the Test Run.
    # Arguments:
    #   limit: the maximum amount of Preconditions to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    preconditions(limit: Int!, start: Int): TestRunPreconditionResults 
    
    # Test of the Test Run.
    test: Test 
    
    # Test version of the Test Run.
    testVersion: TestVersion 
    
    # Test Execution of the Test Run.
    testExecution: TestExecution 
    
    # Date when the test run was last modified.
    lastModified: String 
    
    # Custom Fields of the Test Run.
    customFields: [TestRunCustomFieldValue] 
    
    # Parameters of the Test Run.
    parameters: [TestRunParameter] 
    
    # Iterations of the Test Run.
    # Arguments:
    #   limit: the maximum amount of iterations to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    iterations(limit: Int!, start: Int): TestRunIterationResults 
}
```

### ProjectSettingsTestRunCustomField

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/projectsettingstestruncustomfield.doc.html

Project Test Run Custom Field Settings type.

```graphql
type ProjectSettingsTestRunCustomField {
    # Id
    id: String 
    
    # Name
    name: String 
    
    # Type
    type: String 
    
    # Is the field required
    required: Boolean 
    
    # Values
    values: [String] 
}
```

### ProjectSettingsTestRunCustomFields

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/projectsettingstestruncustomfields.doc.html

Project Test Run Custom Field Field Settings type.

### TestRunCustomFieldValue

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testruncustomfieldvalue.doc.html

Custom Fields Type for Test Runs.

```graphql
type TestRunCustomFieldValue {
    id: String 
    name: String 
    values: JSON 
}
```

### TestRunCustomStepField

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testruncustomstepfield.doc.html

Step CustomField type.

```graphql
type TestRunCustomStepField {
    # Id of the Custom Field.
    id: String 
    
    # Name of the Custom Field.
    name: String 
    
    # Value of the Custom Field.
    value: JSON 
}
```

### TestRunIteration

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testruniteration.doc.html

Test Run iteration type.

```graphql
type TestRunIteration {
    # Rank of the iteration.
    rank: String 
    
    # Parameters of the iteration.
    parameters: [TestRunParameter] 
    
    # Status of the iteration.
    status: StepStatus 
    
    # Step results of the iteration.
    # Arguments:
    #   limit: the maximum amount of step results to be returned. The maximum is 100.
    #   start: the index of the first item to return in the page of results (page offset).
    stepResults(limit: Int!, start: Int): TestRunIterationStepResults 
}
```

### TestRunIterationResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testruniterationresults.doc.html

Test Run iterations results type.

```graphql
type TestRunIterationResults {
    # Total amount of iterations.
    total: Int 
    
    # Index of the first item to return in the page of results (page offset).
    start: Int 
    
    # Maximum amount of iterations to be returned. The maximum is 100.
    limit: Int 
    
    # Iteration results.
    results: [TestRunIteration] 
}
```

### TestRunIterationStepResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testruniterationstepresult.doc.html

Test Run iteration step result type.

```graphql
type TestRunIterationStepResult {
    # Id of the Test Run step.
    id: String 
    
    # Status of the Test Run step.
    status: StepStatus 
    
    # Comment of the Test Run step.
    comment: String 
    
    # Evidence of the Test Run step.
    evidence: [Evidence] 
    
    # Defects of the Test Run step.
    defects: [String] 
    
    # Actual Result of the Test Run step.
    actualResult: String 
}
```

### TestRunIterationStepResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testruniterationstepresults.doc.html

Test Run iteration step results results type.

```graphql
type TestRunIterationStepResults {
    # Total amount of steps.
    total: Int 
    
    # Index of the first item to return in the page of results (page offset).
    start: Int 
    
    # Maximum amount of step results to be returned. The maximum is 100.
    limit: Int 
    
    # Step results.
    results: [TestRunIterationStepResult] 
}
```

### TestRunParameter

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrunparameter.doc.html

Test Run parameter type.

```graphql
type TestRunParameter {
    name: String 
    value: String 
}
```

### TestRunPrecondition

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrunprecondition.doc.html

Test Run Precondition type.

```graphql
type TestRunPrecondition {
    # Precondition of the Test Run.
    preconditionRef: Precondition 
    
    # Precondition definition.
    definition: String 
}
```

### TestRunPreconditionResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrunpreconditionresults.doc.html

Precondition Results type.

```graphql
type TestRunPreconditionResults {
    # Total amount of preconditions.
    total: Int 
    
    # Index of the first item to return in the page of results (page offset).
    start: Int 
    
    # Maximum amount of Preconditions to be returned. The maximum is 100.
    limit: Int 
    
    # Precondition results.
    results: [TestRunPrecondition] 
}
```

### TestRunResults

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrunresults.doc.html

Test Run Results type.

```graphql
type TestRunResults {
    # Total amount of Test Runs.
    total: Int 
    
    # The index of the first item to return in the page of results (page offset).
    start: Int 
    
    # The maximum amount of Test Runs to be returned. The maximum is 100.
    limit: Int 
    
    # Test Run results.
    results: [TestRun] 
}
```

### TestRunStep

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrunstep.doc.html

Test Run Step Type.

```graphql
type TestRunStep {
    # Id of the Test Run Step.
    id: String 
    
    # Status of the Test Run Step.
    status: StepStatus 
    
    # Action of the Test Run Step.
    action: String 
    
    # Data of the Test Run Step.
    data: String 
    
    # Result of the Test Run Step.
    result: String 
    
    # Custom Fields of the Test Run Step.
    customFields: [TestRunCustomStepField] 
    
    # Comment of the Test Run Step.
    comment: String 
    
    # Evidence of the Test Run Step.
    evidence: [Evidence] 
    
    # Attachments of the Test Run Step.
    attachments: [Attachment] 
    
    # Defects of the Test Run Step.
    defects: [String] 
    
    # Actual Result of the Test Run Step.
    actualResult: String 
}
```

### UpdateTestRunExampleStatusResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunexamplestatusresult.doc.html

Update Test Run Example Status Result Type.

### UpdateTestRunResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunresult.doc.html

Update Test Run Result Type.

```graphql
type UpdateTestRunResult {
    # Warnings generated during the operation.
    warnings: [String] 
}
```

### UpdateTestRunStepResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunstepresult.doc.html

Update Test Run Step Result Type.

```graphql
type UpdateTestRunStepResult {
    # Ids of the added Defects.
    addedDefects: [String] 
    
    # Ids of the removed Defects.
    removedDefects: [String] 
    
    # Ids of the added Evidence.
    addedEvidence: [String] 
    
    # Ids of the removed Evidence.
    removedEvidence: [String] 
    
    # Warnings generated during the operation.
    warnings: [String] 
}
```

### UpdateTestRunStepStatusResult

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunstepstatusresult.doc.html

Update Test Run Step Status Result Type.

```graphql
type UpdateTestRunStepStatusResult {
    # Warnings generated during the operation.
    warnings: [String] 
}
```

---

## Input Objects

### TestRunDefectOperationsInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrundefectoperationsinput.doc.html

Test Run Defect Operations Input.

```graphql
input TestRunDefectOperationsInput {
    # Defects to add to the Test Run Step.
    add: [String]
    
    # Defects to remove from the Test Run Step.
    remove: [String]
}
```

### TestRunEvidenceOperationsInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/testrunevidenceoperationsinput.doc.html

Test Run Evidence Operations Input.

```graphql
input TestRunEvidenceOperationsInput {
    # Evidence to add to the Test Run Step.
    add: [AttachmentDataInput]
    
    # Evidence ids to remove from the Test Run Step.
    removeIds: [String]
    
    # Evidence filenames to remove from the Test Run Step.
    removeFilenames: [String]
}
```

### UpdateTestRunStepInput

**Category:** Input Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/updatetestrunstepinput.doc.html

Update Test Run Step Input.

```graphql
input UpdateTestRunStepInput {
    # Comment to add to the Test Run Step.
    comment: String
    
    # Status to set to the Test Run Step.
    status: String
    
    # Evidence of the Test Run Step.
    evidence: TestRunEvidenceOperationsInput
    
    # Defects of the Test Run Step.
    defects: TestRunDefectOperationsInput
    
    # Actual Result of the Test Run Step.
    actualResult: String
}
```