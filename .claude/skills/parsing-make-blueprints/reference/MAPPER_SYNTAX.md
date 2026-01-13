# Make.com Mapper Syntax Reference

Complete reference for Make.com mapper syntax and how to parse mapper references.

## Mapper Syntax

Make.com uses **mapper references** to connect data between modules. The syntax is:

```
{{module_id.field}}
```

or

```
{{module_id}}
```

### Format

- **`{{`**: Opening delimiter (double curly braces)
- **`module_id`**: Integer ID of the source module (1-indexed)
- **`.`** (optional): Field separator
- **`field`** (optional): Field name from source module output
- **`}}`**: Closing delimiter (double curly braces)

## Examples

### Basic References

```
{{1}}                    // Entire output from module 1
{{1.output}}            // `output` field from module 1
{{2.value}}             // `value` field from module 2
{{3.data.results}}      // Nested field path
```

### In Strings

Mapper references can appear inside strings:

```json
{
  "input": "Context: {{1.CONTEXT}}\nInput: {{3.value}}"
}
```

**Parsed as**: "Context: [value from module 1's CONTEXT field]\nInput: [value from module 3's value field]"

### In Nested Objects

Mapper references can appear in nested objects and arrays:

```json
{
  "tools": [
    {
      "type": "web_search_preview",
      "search_context": "{{2.context}}"
    }
  ]
}
```

## Parsing Mapper References

### Regex Pattern

Use this regex pattern to extract mapper references:

```python
pattern = r'\{\{(\d+)(?:\.(\w+))?\}\}'
```

**Explanation**:
- `\{\{` - Match opening `{{`
- `(\d+)` - Capture module ID (one or more digits)
- `(?:\.(\w+))?` - Optional group for field name (`.` followed by word characters)
- `\}\}` - Match closing `}}`

### Python Example

```python
import re

mapper_str = json.dumps(mapper)
pattern = r'\{\{(\d+)(?:\.(\w+))?\}\}'

matches = re.findall(pattern, mapper_str)
# Returns: [('1', 'output'), ('2', 'value'), ('3', '')]

for match in matches:
    source_module_id = int(match[0])  # Module ID
    field = match[1] if match[1] else "output"  # Field name or default
```

## Building Dependency Graph

### Step 1: Extract All References

For each module, extract all mapper references from its mapper object:

```python
def extract_inputs(mapper, current_module_id):
    inputs = []
    mapper_str = json.dumps(mapper)
    pattern = r'\{\{(\d+)(?:\.(\w+))?\}\}'
    
    matches = re.findall(pattern, mapper_str)
    for match in matches:
        source_module_id = int(match[0])
        field = match[1] if match[1] else "output"
        
        if source_module_id != current_module_id:
            inputs.append({
                "module_id": source_module_id,
                "field": field
            })
    
    return inputs
```

### Step 2: Build Dependency Graph

```python
dependencies = defaultdict(list)  # target -> [sources]

for module in flow:
    module_id = module.get("id")
    inputs = extract_inputs(module.get("mapper", {}), module_id)
    
    for inp in inputs:
        dependencies[module_id].append({
            "source_module_id": inp["module_id"],
            "field": inp["field"]
        })
```

### Step 3: Track Data Transformations

```python
transformations = []

for module in flow:
    module_id = module.get("id")
    inputs = extract_inputs(module.get("mapper", {}), module_id)
    
    for inp in inputs:
        transformations.append({
            "from": {
                "id": inp["module_id"],
                "field": inp["field"]
            },
            "to": {
                "id": module_id
            }
        })
```

## Common Patterns

### Sequential Flow

Modules that reference previous modules:

```
Module 1 → Module 2 ({{1.output}}) → Module 3 ({{2.result}})
```

**Pattern**: Each module references the previous one.

### Parallel Execution

Multiple modules referencing the same source:

```
Module 1 → Module 2 ({{1.output}})
         → Module 3 ({{1.output}})
         → Module 4 ({{1.output}})
```

**Pattern**: Multiple modules reference the same source module.

### Conditional Flow

Router/filter modules with conditions:

```json
{
  "module": "flow-control:router",
  "mapper": {
    "routes": [
      {
        "condition": "{{1.status}} == 'success'",
        "output": "{{1.data}}"
      },
      {
        "condition": "{{1.status}} == 'error'",
        "output": "{{1.error}}"
      }
    ]
  }
}
```

**Pattern**: Router/filter modules with conditional mapper references.

### Subscenarios

Sub-workflows with input parameters:

```json
{
  "module": "scenario-service:CallSubscenario",
  "mapper": {
    "scenarioId": "12345",
    "input1": "{{1.data}}",
    "input2": "{{2.value}}"
  }
}
```

**Pattern**: Subscenario modules pass data via mapper parameters.

## Edge Cases

### Self-References

Modules can reference themselves:

```
{{4.previous_value}}
```

**Handling**: Filter out self-references when building dependency graph.

### Missing Fields

If field is not specified, it refers to entire output:

```
{{1}}  // Entire output from module 1
```

**Handling**: Use default field name `"output"` or `""`.

### Nested References

References can appear in nested structures:

```json
{
  "nested": {
    "deep": {
      "value": "{{1.output}}"
    }
  }
}
```

**Handling**: Convert entire mapper to string for pattern matching.

### String Concatenation

References can be concatenated:

```
"{{1.prefix}}_{{2.suffix}}"
```

**Handling**: Extract both references separately.

## Data Flow Tracking

### Finding Potential Data Loss

Modules whose output is never referenced:

```python
all_source_ids = set()
for deps in dependencies.values():
    for dep in deps:
        all_source_ids.add(dep["source_module_id"])

used_module_ids = set(dependencies.keys()) | all_source_ids

# Find unused outputs
unused = []
for module in flow:
    module_id = module.get("id")
    if module_id not in used_module_ids:
        unused.append(module_id)
```

### Finding Circular Dependencies

Check for circular references in dependency graph:

```python
def has_circular_dependency(dependencies, start_id, visited=None, rec_stack=None):
    if visited is None:
        visited = set()
    if rec_stack is None:
        rec_stack = set()
    
    visited.add(start_id)
    rec_stack.add(start_id)
    
    for dep in dependencies.get(start_id, []):
        source_id = dep["source_module_id"]
        if source_id not in visited:
            if has_circular_dependency(dependencies, source_id, visited, rec_stack):
                return True
        elif source_id in rec_stack:
            return True
    
    rec_stack.remove(start_id)
    return False
```

## Best Practices

1. **Convert mapper to string**: Use `json.dumps()` to handle nested structures
2. **Extract all references**: Find all occurrences, not just first match
3. **Filter self-references**: Exclude references where source == target
4. **Handle missing fields**: Default to `"output"` or empty string
5. **Build complete graph**: Track all dependencies for full data flow analysis
6. **Preserve original paths**: Always include original JSON path in output for verification

