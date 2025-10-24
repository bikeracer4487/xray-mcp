"""Simple GraphQL query templates for Xray operations."""

# Test Operations
CREATE_MANUAL_TEST = """
mutation CreateTest($projectKey: String!, $summary: String!, $description: String, $steps: [CreateStepInput!]) {
    createTest(
        testType: { name: "Manual" }
        jira: {
            fields: {
                summary: $summary
                description: $description
                project: { key: $projectKey }
            }
        }
        steps: $steps
    ) {
        test {
            issueId
            testType { name }
            jira(fields: ["key", "summary"])
        }
        warnings
    }
}
"""

CREATE_GENERIC_TEST = """
mutation CreateTest($projectKey: String!, $summary: String!, $description: String) {
    createTest(
        testType: { name: "Generic" }
        jira: {
            fields: {
                summary: $summary
                description: $description
                project: { key: $projectKey }
            }
        }
    ) {
        test {
            issueId
            testType { name }
            jira(fields: ["key", "summary"])
        }
        warnings
    }
}
"""

CREATE_CUCUMBER_TEST = """
mutation CreateTest($projectKey: String!, $summary: String!, $description: String, $gherkin: String!) {
    createTest(
        testType: { name: "Cucumber" }
        jira: {
            fields: {
                summary: $summary
                description: $description
                project: { key: $projectKey }
            }
        }
        gherkin: $gherkin
    ) {
        test {
            issueId
            testType { name }
            jira(fields: ["key", "summary"])
        }
        warnings
    }
}
"""

GET_TEST = """
query GetTest($issueId: String!) {
    getTest(issueId: $issueId) {
        issueId
        testType { name }
        jira(fields: ["key", "summary", "description"])
        steps {
            id
            action
            data
            result
        }
        gherkin
        lastModified
    }
}
"""

LIST_TESTS = """
query GetTests($jql: String!, $limit: Int!, $start: Int!) {
    getTests(jql: $jql, limit: $limit, start: $start) {
        total
        start
        limit
        results {
            issueId
            testType { name }
            jira(fields: ["key", "summary", "description"])
            lastModified
        }
    }
}
"""

DELETE_TEST = """
mutation DeleteTest($issueId: String!) {
    deleteTest(issueId: $issueId)
}
"""

# Test Execution Operations
CREATE_TEST_EXECUTION = """
mutation CreateTestExecution($projectKey: String!, $summary: String!, $testIssueIds: [String!], $testEnvironments: [String!]) {
    createTestExecution(
        testIssueIds: $testIssueIds
        testEnvironments: $testEnvironments
        jira: {
            fields: {
                summary: $summary
                project: { key: $projectKey }
            }
        }
    ) {
        testExecution {
            issueId
            testEnvironments
            jira(fields: ["key", "summary"])
        }
        warnings
        createdTestEnvironments
    }
}
"""

GET_TEST_EXECUTION = """
query GetTestExecution($issueId: String!) {
    getTestExecution(issueId: $issueId) {
        issueId
        projectId
        testEnvironments
        jira(fields: ["key", "summary", "description"])
        tests(limit: 100) {
            total
            results {
                issueId
                testType { name }
                jira(fields: ["key", "summary"])
            }
        }
    }
}
"""

LIST_TEST_EXECUTIONS = """
query GetTestExecutions($jql: String!, $limit: Int!, $start: Int!) {
    getTestExecutions(jql: $jql, limit: $limit, start: $start) {
        total
        start
        limit
        results {
            issueId
            projectId
            testEnvironments
            jira(fields: ["key", "summary", "created", "updated"])
        }
    }
}
"""

DELETE_TEST_EXECUTION = """
mutation DeleteTestExecution($issueId: String!) {
    deleteTestExecution(issueId: $issueId)
}
"""

ADD_TESTS_TO_EXECUTION = """
mutation AddTestsToTestExecution($issueId: String!, $testIssueIds: [String!]!) {
    addTestsToTestExecution(issueId: $issueId, testIssueIds: $testIssueIds) {
        addedTests
        warning
    }
}
"""

REMOVE_TESTS_FROM_EXECUTION = """
mutation RemoveTestsFromTestExecution($issueId: String!, $testIssueIds: [String!]!) {
    removeTestsFromTestExecution(issueId: $issueId, testIssueIds: $testIssueIds)
}
"""

# Test Plan Operations
CREATE_TEST_PLAN = """
mutation CreateTestPlan($projectKey: String!, $summary: String!, $testIssueIds: [String!]) {
    createTestPlan(
        testIssueIds: $testIssueIds
        jira: {
            fields: {
                summary: $summary
                project: { key: $projectKey }
            }
        }
    ) {
        testPlan {
            issueId
            jira(fields: ["key", "summary"])
        }
        warnings
    }
}
"""

GET_TEST_PLAN = """
query GetTestPlan($issueId: String!) {
    getTestPlan(issueId: $issueId) {
        issueId
        projectId
        jira(fields: ["key", "summary", "description"])
        tests(limit: 100) {
            total
            results {
                issueId
                testType { name }
                jira(fields: ["key", "summary"])
            }
        }
    }
}
"""

LIST_TEST_PLANS = """
query GetTestPlans($jql: String!, $limit: Int!, $start: Int!) {
    getTestPlans(jql: $jql, limit: $limit, start: $start) {
        total
        start
        limit
        results {
            issueId
            projectId
            jira(fields: ["key", "summary", "created", "updated"])
        }
    }
}
"""

DELETE_TEST_PLAN = """
mutation DeleteTestPlan($issueId: String!) {
    deleteTestPlan(issueId: $issueId)
}
"""

ADD_TESTS_TO_PLAN = """
mutation AddTestsToTestPlan($issueId: String!, $testIssueIds: [String!]!) {
    addTestsToTestPlan(issueId: $issueId, testIssueIds: $testIssueIds) {
        addedTests
        warning
    }
}
"""

REMOVE_TESTS_FROM_PLAN = """
mutation RemoveTestsFromTestPlan($issueId: String!, $testIssueIds: [String!]!) {
    removeTestsFromTestPlan(issueId: $issueId, testIssueIds: $testIssueIds)
}
"""

ADD_EXECUTIONS_TO_PLAN = """
mutation AddTestExecutionsToTestPlan($issueId: String!, $testExecIssueIds: [String!]!) {
    addTestExecutionsToTestPlan(issueId: $issueId, testExecIssueIds: $testExecIssueIds) {
        addedTestExecutions
        warning
    }
}
"""

REMOVE_EXECUTIONS_FROM_PLAN = """
mutation RemoveTestExecutionsFromTestPlan($issueId: String!, $testExecIssueIds: [String!]!) {
    removeTestExecutionsFromTestPlan(issueId: $issueId, testExecIssueIds: $testExecIssueIds)
}
"""

# Test Run Operations
GET_TEST_RUN = """
query GetTestRun($testExecIssueId: String!, $testIssueId: String!) {
    getTestRun(testExecIssueId: $testExecIssueId, testIssueId: $testIssueId) {
        id
        status { name color description }
        comment
        startedOn
        finishedOn
        executedById
        assigneeId
        evidence { id filename }
        defects
        test { issueId }
        testExecution { issueId }
    }
}
"""

LIST_TEST_RUNS = """
query GetTestRuns($testIssueIds: [String], $testExecIssueIds: [String], $limit: Int!) {
    getTestRuns(testIssueIds: $testIssueIds, testExecIssueIds: $testExecIssueIds, limit: $limit) {
        total
        start
        limit
        results {
            id
            status { name color }
            comment
            startedOn
            finishedOn
            test { issueId }
            testExecution { issueId }
        }
    }
}
"""

UPDATE_TEST_RUN_STATUS = """
mutation UpdateTestRunStatus($id: String!, $status: String!) {
    updateTestRunStatus(id: $id, status: $status)
}
"""

UPDATE_TEST_RUN_COMMENT = """
mutation UpdateTestRunComment($id: String!, $comment: String!) {
    updateTestRunComment(id: $id, comment: $comment)
}
"""

ADD_DEFECTS_TO_TEST_RUN = """
mutation AddDefectsToTestRun($id: String!, $issues: [String]!) {
    addDefectsToTestRun(id: $id, issues: $issues) {
        addedDefects
        warnings
    }
}
"""

# Test Update Operations
UPDATE_TEST_TYPE = """
mutation UpdateTestType($issueId: String!, $testType: UpdateTestTypeInput!) {
    updateTestType(issueId: $issueId, testType: $testType) {
        issueId
        testType {
            name
        }
    }
}
"""

UPDATE_UNSTRUCTURED_TEST_DEFINITION = """
mutation UpdateUnstructuredTestDefinition($issueId: String!, $unstructured: String!) {
    updateUnstructuredTestDefinition(issueId: $issueId, unstructured: $unstructured) {
        warnings
    }
}
"""

UPDATE_GHERKIN_TEST_DEFINITION = """
mutation UpdateGherkinTestDefinition($issueId: String!, $gherkin: String!) {
    updateGherkinTestDefinition(issueId: $issueId, gherkin: $gherkin) {
        issueId
    }
}
"""

UPDATE_TEST_METADATA = """
mutation UpdateTest($issueId: String!, $summary: String, $description: String) {
    updateTest(
        issueId: $issueId
        jira: {
            fields: {
                summary: $summary
                description: $description
            }
        }
    ) {
        test {
            issueId
            jira(fields: ["key", "summary", "description"])
        }
        warnings
    }
}
"""

# Test Environment Operations
ADD_TEST_ENVIRONMENTS_TO_EXECUTION = """
mutation AddTestEnvironmentsToTestExecution($issueId: String!, $testEnvironments: [String!]!) {
    addTestEnvironmentsToTestExecution(issueId: $issueId, testEnvironments: $testEnvironments) {
        associatedTestEnvironments
        createdTestEnvironments
        warning
    }
}
"""

REMOVE_TEST_ENVIRONMENTS_FROM_EXECUTION = """
mutation RemoveTestEnvironmentsFromTestExecution($issueId: String!, $testEnvironments: [String!]!) {
    removeTestEnvironmentsFromTestExecution(issueId: $issueId, testEnvironments: $testEnvironments)
}
"""