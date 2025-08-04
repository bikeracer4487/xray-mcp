# Xray GraphQL API Documentation

This directory contains the complete documentation for Xray's GraphQL API.

## Complete Reference Guides

The following consolidated reference guides provide comprehensive documentation for each major API area:

- **[TESTS_COMPLETE_REFERENCE.md](TESTS_COMPLETE_REFERENCE.md)** - All test-related queries, mutations, and objects
- **[TESTRUN_COMPLETE_REFERENCE.md](TESTRUN_COMPLETE_REFERENCE.md)** - Complete TestRun operations and types
- **[TESTEXECUTION_COMPLETE_REFERENCE.md](TESTEXECUTION_COMPLETE_REFERENCE.md)** - TestExecution management documentation
- **[TESTPLANS_COMPLETE_REFERENCE.md](TESTPLANS_COMPLETE_REFERENCE.md)** - TestPlan operations and objects
- **[TESTSETS_COMPLETE_REFERENCE.md](TESTSETS_COMPLETE_REFERENCE.md)** - TestSet functionality reference
- **[TESTSTEP_COMPLETE_REFERENCE.md](TESTSTEP_COMPLETE_REFERENCE.md)** - TestStep operations and types
- **[PRECONDITIONS_COMPLETE_REFERENCE.md](PRECONDITIONS_COMPLETE_REFERENCE.md)** - Precondition management reference
- **[FOLDERS_COMPLETE_REFERENCE.md](FOLDERS_COMPLETE_REFERENCE.md)** - Folder/Test Repository operations
- **[DATASETS_COMPLETE_REFERENCE.md](DATASETS_COMPLETE_REFERENCE.md)** - Dataset management documentation

## Individual API Components

### Queries

Coverage and Project Settings:
- [getCoverableIssue](queries/getcoverableissue.md)
- [getCoverableIssues](queries/getcoverableissues.md)
- [getIssueLinkTypes](queries/getissuelinktypes.md)
- [getProjectSettings](queries/getprojectsettings.md)
- [getStatus](queries/getstatus.md)
- [getStatuses](queries/getstatuses.md)

### Mutations

Remaining standalone mutations:
- [updateGherkinTestDefinition](mutations/updategherkintestdefinition.md)
- [updateIterationStatus](mutations/updateiterationstatus.md)

### Objects

Core Types:
- [Attachment](objects/attachment.md)
- [Evidence](objects/evidence.md)
- [Example](objects/example.md)
- [Parameter](objects/parameter.md)
- [Status](objects/status.md)

Coverage Objects:
- [CoverableIssue](objects/coverableissue.md)
- [CoverableIssueResults](objects/coverableissueresults.md)
- [CoverageStatus](objects/coveragestatus.md)

Result Objects:
- [AddDefectsResult](objects/adddefectsresult.md)
- [AddEvidenceResult](objects/addevidenceresult.md)
- [AddPreconditionsResult](objects/addpreconditionsresult.md)
- [AddTestEnvironmentsResult](objects/addtestenvironmentsresult.md)
- [AddTestsResult](objects/addtestsresult.md)
- [CreatePreconditionResult](objects/createpreconditionresult.md)
- [RemoveDefectsResult](objects/removedefectsresult.md)
- [RemoveEvidenceResult](objects/removeevidenceresult.md)
- [UpdateIterationStatusResult](objects/updateiterationstatusresult.md)

Project Settings:
- [ProjectSettings](objects/projectsettings.md)
- [ProjectSettingsTestCoverage](objects/projectsettingstestcoverage.md)

Execution Results:
- [Result](objects/result.md)
- [ResultsEmbedding](objects/resultsembedding.md)
- [ResultsExample](objects/resultsexample.md)

History and Metadata:
- [Changes](objects/changes.md)
- [IssueLinkType](objects/issuelinktype.md)
- [XrayHistoryEntry](objects/xrayhistoryentry.md)
- [XrayHistoryResults](objects/xrayhistoryresults.md)
- [PreconditionResults](objects/preconditionresults.md)

GraphQL Schema Objects:
- [__Directive](objects/directive.md)
- [__EnumValue](objects/enumvalue.md)
- [__Field](objects/field.md)
- [__InputValue](objects/inputvalue.md)
- [__Schema](objects/schema.md)
- [__Type](objects/type.md)

### Input Objects

- [AttachmentDataInput](input_objects/attachmentdatainput.md)
- [AttachmentInput](input_objects/attachmentinput.md)
- [AttachmentOperationsInput](input_objects/attachmentoperationsinput.md)
- [CustomFieldInput](input_objects/customfieldinput.md)
- [TestTypeInput](input_objects/testtypeinput.md)
- [TestWithVersionInput](input_objects/testwithversioninput.md)
- [UpdateTestTypeInput](input_objects/updatetesttypeinput.md)

### Scalars

- [Boolean](scalars/boolean.md)
- [Float](scalars/float.md)
- [Int](scalars/int.md)
- [JSON](scalars/json.md)
- [String](scalars/string.md)

### Enums

- [__DirectiveLocation](enums/directivelocation.md)
- [__TypeKind](enums/typekind.md)

## Usage Guide

For most use cases, start with the consolidated reference guides listed at the top of this document. These provide:

1. **Complete API coverage** for each major area (Tests, TestRuns, TestExecutions, etc.)
2. **All related queries, mutations, and objects** in one place
3. **GraphQL schema definitions** with examples
4. **Cross-references** between related operations

The individual component files are preserved for specific lookups and remain part of the complete API documentation.

## API Organization

The Xray GraphQL API is organized around these main entities:

- **Tests** - Test case definitions and management
- **TestRuns** - Individual test execution instances
- **TestExecutions** - Test execution cycles/sessions
- **TestPlans** - Test planning and organization
- **TestSets** - Logical groupings of tests
- **TestSteps** - Step definitions within tests
- **Preconditions** - Prerequisites for test execution
- **Folders** - Hierarchical organization (Test Repository)
- **Datasets** - Data-driven testing support

Each consolidated reference guide provides comprehensive documentation for working with these entities.