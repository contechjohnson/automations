# Make.com JSON Structure Documentation

Complete reference for Make.com blueprint JSON structure.

## Top-Level Structure

Make.com blueprint JSON files have the following top-level structure:

```json
{
  "name": "Workflow Name",
  "flow": [
    // Array of modules
  ]
}
```

### Fields

- **`name`** (string): Workflow/scenario name
- **`flow`** (array): Array of module objects representing the workflow steps

## Module Structure

Each module in the `flow` array has the following structure:

```json
{
  "id": 1,
  "module": "module-type:operation",
  "version": 2,
  "parameters": {
    "__IMTCONN__": 1234567
  },
  "mapper": {
    "field": "value",
    "nestedField": "{{1.output}}"
  },
  "metadata": {
    "designer": {
      "x": 0,
      "y": 0,
      "name": "Module Name"
    },
    "restore": {
      // UI state for restoration
    }
  }
}
```

### Module Fields

- **`id`** (integer): Unique module identifier (1-indexed)
- **`module`** (string): Module type and operation (e.g., `openai-gpt-3:createModelResponse`, `google-sheets:getCell`)
- **`version`** (integer): Module version
- **`parameters`** (object): Connection/auth parameters (e.g., `__IMTCONN__` for connections)
- **`mapper`** (object): **Key field** - Data mapping between modules. Contains:
  - Static values
  - Mapper references: `{{module_id.field}}` or `{{module_id}}`
- **`metadata`** (object): UI and restore information
  - **`designer`**: Visual positioning and custom names
    - `x`, `y`: Position coordinates
    - `name`: Custom module name (if set)
  - **`restore`**: UI state for restoration (can be ignored for business logic)

## Key Concepts

### Mapper References

Make.com uses **implicit connections** via mapper references, not explicit connection arrays like n8n.

**Syntax**: `{{module_id.field}}` or `{{module_id}}`

**Examples**:
- `{{1.output}}` - References output from module 1
- `{{2.value}}` - References `value` field from module 2
- `{{3}}` - References entire output object from module 3

**Parsing**:
- Use regex pattern: `r'\{\{(\d+)(?:\.(\w+))?\}\}'`
- Extract module ID and field name
- Build dependency graph from these references

### Module Types

See `MODULE_TYPES.md` for complete list of module types.

### Data Flow

Data flows between modules via:
1. **Mapper references** - `{{module_id.field}}` in mapper objects
2. **Implicit connections** - Modules execute in order, later modules can reference earlier ones
3. **Variables** - SetVariable/GetVariable modules for shared state

## How to Double-Check Original JSON

The converter always includes the original JSON file path in the output report.

### To verify the conversion:

1. **Locate original file**: Use the path in the report's "Original JSON" field
2. **Open in text editor**: JSON files are readable
3. **Search for module**: Use module ID or name to find specific modules
4. **Verify mapper**: Check mapper object for data flow references
5. **Compare with report**: Ensure module counts, types, and relationships match

### Common Issues

- **Missing modules**: Check if report shows fewer modules than expected
- **Incorrect data flow**: Verify mapper references in original JSON
- **Wrong module type**: Check `module` field in JSON vs. report category

### Quick Verification Commands

```bash
# Count modules in JSON
jq '.flow | length' path/to/blueprint.json

# List all module types
jq '.flow[].module' path/to/blueprint.json | sort | uniq

# Find specific module by ID
jq '.flow[] | select(.id == 1)' path/to/blueprint.json

# Extract all mapper references
grep -o '{{[^}]*}}' path/to/blueprint.json | sort | uniq
```

## Common Pitfalls

1. **Ignore `restore` metadata**: Contains only UI state, not business logic
2. **Parameter values**: `__IMTCONN__` values are connection IDs, not business logic
3. **Nested mapper references**: Can appear in strings or nested objects
4. **Module ordering**: Modules in `flow` array follow execution order, but connections determine actual dependencies
5. **Missing connections**: Some modules may not have explicit references but still depend on earlier modules

## Example Module

```json
{
  "id": 4,
  "module": "openai-gpt-3:createModelResponse",
  "version": 1,
  "parameters": {
    "__IMTCONN__": 5375337
  },
  "mapper": {
    "input": "<CONTEXT>\n{{1.CONTEXT}}\n</CONTEXT>\n<INPUT>\n{{3.value}}\n</INPUT>",
    "model": "gpt-4.1",
    "instructions": "{{2.value}}",
    "max_output_tokens": "10000"
  },
  "metadata": {
    "designer": {
      "x": 900,
      "y": 0,
      "name": "SEARCH_BUILDER"
    }
  }
}
```

**Analysis**:
- Module ID: 4
- Type: LLM call (OpenAI GPT-3)
- Inputs: Module 1 (CONTEXT field), Module 3 (value field)
- Configuration: Model `gpt-4.1`, max tokens 10000
- Instructions: System prompt from Module 2 (value field)

