# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Directory Overview

This directory contains comprehensive GraphQL API documentation for XRAY Cloud's test management system. It serves as the complete reference for developers integrating with XRAY's GraphQL API.

## Documentation Structure

```
xray-docs/
├── *_COMPLETE_REFERENCE.md    # Consolidated guides by entity type
├── queries/                   # Individual query documentation
├── mutations/                 # Individual mutation documentation
├── objects/                   # GraphQL object type definitions
├── input_objects/            # Input type definitions
├── scalars/                  # Scalar type definitions
├── enums/                    # Enumeration definitions
└── download_xray_docs_v2.py # Documentation scraper/generator
```

## Key Commands

### Documentation Generation
```bash
# Download/update documentation from XRAY Cloud
python3 download_xray_docs_v2.py

# Update specific missing pages
./download-remaining.sh
```

## Architecture & Organization

### 1. Complete Reference Guides
The primary documentation is organized into consolidated reference files by entity:
- **TESTS_COMPLETE_REFERENCE.md** - Test case operations (queries, mutations, objects)
- **TESTRUN_COMPLETE_REFERENCE.md** - Test execution instances
- **TESTEXECUTION_COMPLETE_REFERENCE.md** - Test cycles/sessions
- **TESTPLANS_COMPLETE_REFERENCE.md** - Test planning functionality
- **TESTSETS_COMPLETE_REFERENCE.md** - Test grouping operations
- **TESTSTEP_COMPLETE_REFERENCE.md** - Step-level operations
- **PRECONDITIONS_COMPLETE_REFERENCE.md** - Prerequisites management
- **FOLDERS_COMPLETE_REFERENCE.md** - Test Repository hierarchy
- **DATASETS_COMPLETE_REFERENCE.md** - Data-driven testing

Each consolidated guide includes:
- All related queries with GraphQL schemas
- All related mutations with examples
- Object type definitions
- Cross-references between operations

### 2. Individual Documentation Files
Located in subdirectories for granular reference:
- **queries/** - Individual query operations
- **mutations/** - Individual mutation operations
- **objects/** - GraphQL object types
- **input_objects/** - Input type definitions

### 3. Documentation Patterns
All documentation follows consistent patterns:
```graphql
# Query example structure
query {
    getTest(issueId: "12345") {
        issueId
        testType { name }
        steps {
            action
            data
            result
        }
    }
}
```

## Important Technical Details

### GraphQL API Constraints
- **Pagination**: Maximum 100 items per query
- **JQL Limits**: Queries returning >100 issues will error
- **Field Selection**: Use specific field lists to optimize responses
- **Nested Queries**: Test versions only accessible through expanded queries

### Common Query Patterns
```graphql
# Basic test retrieval
getTest(issueId: "12345")

# Paginated test search
getTests(jql: "project = PROJ", limit: 50, start: 0)

# Expanded test with versions
getExpandedTest(issueId: "12345", versionsCursor: "...", versionsLimit: 10)
```

### Authentication Context
All GraphQL operations require OAuth 2.0 Bearer token authentication:
```
Authorization: Bearer <access_token>
```

## Working with the Documentation

### Finding Information
1. **Start with Complete References** - Consolidated guides provide comprehensive coverage
2. **Use Individual Files** - For specific operation details
3. **Check Object Definitions** - Understanding return types and structures
4. **Review Input Objects** - For mutation parameter requirements

### Common Use Cases
- **Test Management**: See TESTS_COMPLETE_REFERENCE.md
- **Execution Tracking**: See TESTRUN_COMPLETE_REFERENCE.md and TESTEXECUTION_COMPLETE_REFERENCE.md
- **Test Organization**: See FOLDERS_COMPLETE_REFERENCE.md and TESTSETS_COMPLETE_REFERENCE.md
- **Planning**: See TESTPLANS_COMPLETE_REFERENCE.md

### Documentation Updates
The documentation is scraped from XRAY Cloud's official API docs. To update:
1. Run `download_xray_docs_v2.py` to fetch latest documentation
2. The script converts HTML to markdown format
3. Manual consolidation may be needed for new entity types