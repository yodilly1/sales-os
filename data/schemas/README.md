# Sales OS Data Schemas

This directory contains JSON Schema definitions for all core data entities in Sales OS.

## Schema Files

### Core Entities
- `user.schema.json` - User, Team, and Organization entities
- `transcript.schema.json` - Call and Transcript entities
- `spiced.schema.json` - SPICED Analysis entity
- `content.schema.json` - Content and ContentTemplate entities
- `prospect.schema.json` - Prospect and Company entities
- `coaching.schema.json` - Coaching Report and Score entities

### Integration Schemas
- `hubspot.schema.json` - HubSpot integration data

## Usage

These schemas can be used for:
1. API request/response validation
2. Frontend form validation
3. Data import/export validation
4. Documentation generation
5. Code generation

## Schema Version

All schemas follow JSON Schema Draft 2020-12 specification.

## Validation

To validate data against these schemas, use any JSON Schema validator:

```python
import jsonschema
import json

with open('data/schemas/user.schema.json') as f:
    schema = json.load(f)

user_data = {...}
jsonschema.validate(instance=user_data, schema=schema)
```
