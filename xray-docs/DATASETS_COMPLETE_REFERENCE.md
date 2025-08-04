# Xray Datasets - Complete Reference

This document consolidates all dataset-related GraphQL operations and types for Xray. Datasets are used for data-driven testing, allowing tests to run with multiple sets of input data.

## Table of Contents

1. [Queries](#queries)
   - [getDataset](#getdataset)
   - [getDatasets](#getdatasets)
2. [Objects](#objects)
   - [Dataset](#dataset-object)
   - [DatasetRow](#datasetrow-object)

---

## Queries

### getDataset

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getdataset.doc.html

Returns a single Dataset for a specific test.

**GraphQL Schema Definition:**

```graphql
{
    getDataset(testIssueId: "12345") {
        id
        parameters {
            name
            type
            listValues
        }
        rows { 
          order 
          Values
        }
    }
}
```

**Example:**

```graphql
{
    getDataset(testIssueId: "12345") {
        id
        parameters {
            name
            type
            listValues
        }
        rows { 
          order 
          Values
        }
    }
}
```

### getDatasets

**Category:** Queries  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/getdatasets.doc.html

Returns multiple Datasets for specified tests, including their metadata and parameters.

**GraphQL Schema Definition:**

```graphql
{
    getDatasets(
        testIssueIds: ["30000", "40000"],
    ) 
      {
        id
        testIssueId  
        testExecIssueId
        testPlanIssueId
        parameters {
            name
            type
            listValues
        }
        rows {
          order
          Values
        }
      }
}
```

**Example:**

```graphql
{
    getDatasets(
        testIssueIds: ["30000", "40000"],
    ) 
      {
        id
        testIssueId  
        testExecIssueId
        testPlanIssueId
        parameters {
            name
            type
            listValues
        }
        rows {
          order
          Values
        }
      }
}
```

---

## Objects

### Dataset Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/dataset.doc.html

Represents a single Dataset entity with its metadata, parameters, and associated dataset rows.

**GraphQL Schema Definition:**

```graphql
type Dataset {
    # Unique identifier of the Dataset.
    id: String

    # The ID of the test issue associated with the Dataset.
    testIssueId: String

    # The ID of the test execution issue associated with the Dataset.
    testExecIssueId: String

    # The ID of the test plan issue associated with the Dataset.
    testPlanIssueId: String

    # The ID of the test step associated with the Dataset (only for test step datasets).
    testStepId: String

    # The ID of the call test issue (only for test step datasets).
    callTestIssueId: String

    # Parameters of the Dataset, represented as an array of key-value pairs.
    parameters: [Parameter]

    # The rows of the Dataset, representing combinatorial data.
    rows: [DatasetRow]
}
```

**Required by:**
- ExpandedTest - Expanded test issue type
- getDataset
- getDatasets
- Query
- Test - Test issue type

### DatasetRow Object

**Category:** Objects  
**Source:** https://us.xray.cloud.getxray.app/doc/graphql/datasetrow.doc.html

Represents a single row in the Dataset, containing combinatorial data.

**GraphQL Schema Definition:**

```graphql
type DatasetRow {
    # The order of the row in the Dataset.
    order: Int

    # The values of the row, stored String array.
    Values: [String]
}
```

**Required by:**
- Dataset - Dataset type

---

## Usage Notes

1. **Data-Driven Testing**: Datasets enable running the same test with different sets of input data
2. **Parameter Types**: Parameters can have various types and may include list values for selection
3. **Row Order**: Dataset rows have an order field to maintain the sequence of test data
4. **Context Associations**: Datasets can be associated with:
   - Test issues (testIssueId)
   - Test execution issues (testExecIssueId)
   - Test plan issues (testPlanIssueId)
   - Test steps (testStepId)
   - Called test issues (callTestIssueId)
5. **Combinatorial Data**: Dataset rows represent different combinations of parameter values for test execution

## Common Use Cases

1. **Parameterized Testing**: Run the same test logic with multiple input/output combinations
2. **Boundary Testing**: Test edge cases by providing boundary values in dataset rows
3. **Cross-Browser Testing**: Use datasets to specify different browser/environment combinations
4. **Localization Testing**: Test with different language/locale combinations
5. **User Role Testing**: Test functionality with different user permissions/roles

This consolidated reference provides all GraphQL operations and types related to Xray Datasets in a single document.