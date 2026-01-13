# Make.com Module Types Reference

Complete reference for Make.com module types and their business logic mappings.

## Module Type Format

Make.com modules follow the format: `{service}:{operation}`

Examples:
- `openai-gpt-3:createModelResponse`
- `google-sheets:getCell`
- `http:request`
- `scenario-service:CallSubscenario`

## Categories

### LLM/AI Modules

| Module Type | Business Logic Description | Key Fields |
|------------|---------------------------|------------|
| `openai-gpt-3:createModelResponse` | LLM call using OpenAI GPT-3 | `model`, `input`, `instructions`, `max_output_tokens` |
| `openai-gpt-4:createModelResponse` | LLM call using OpenAI GPT-4 | `model`, `input`, `instructions`, `max_output_tokens` |
| `openrouter:createModelResponse` | LLM call via OpenRouter | `model`, `input`, `instructions` |

**Configuration**:
- `model`: Model name (e.g., `gpt-4.1`, `gpt-5.2`)
- `input`: User prompt (may contain mapper references)
- `instructions`: System prompt (may contain mapper references)
- `max_output_tokens`: Maximum tokens in response
- `tools`: Array of tool configurations (e.g., web search)
- `background`: Boolean for async execution
- `store`: Boolean to store conversation

### Database Modules

| Module Type | Business Logic Description | Key Fields |
|------------|---------------------------|------------|
| `google-sheets:getCell` | Read cell from Google Sheets | `spreadsheetId`, `sheetId`, `cell` |
| `google-sheets:updateCell` | Update cell in Google Sheets | `spreadsheetId`, `sheetId`, `cell`, `value` |
| `google-sheets:getRow` | Read row from Google Sheets | `spreadsheetId`, `sheetId`, `row` |
| `google-sheets:updateRow` | Update row in Google Sheets | `spreadsheetId`, `sheetId`, `row`, `values` |

**Configuration**:
- `spreadsheetId`: Google Sheets spreadsheet ID
- `sheetId`: Sheet name
- `cell`: Cell reference (e.g., `C2`, `A1`)
- `from`: Drive source (`drive`, `share`, `team`)

### HTTP Modules

| Module Type | Business Logic Description | Key Fields |
|------------|---------------------------|------------|
| `http:request` | HTTP request (GET, POST, PUT, DELETE) | `url`, `method`, `headers`, `body` |
| `http:makeRequest` | Make HTTP request | `url`, `method`, `headers`, `body` |

**Configuration**:
- `url`: Target URL (may contain mapper references)
- `method`: HTTP method (`GET`, `POST`, `PUT`, `DELETE`)
- `headers`: HTTP headers object
- `body`: Request body

### Flow Control Modules

| Module Type | Business Logic Description | Key Fields |
|------------|---------------------------|------------|
| `scenario-service:StartSubscenario` | Start a sub-workflow | `scenarioId`, `scenarioName` |
| `scenario-service:CallSubscenario` | Call a sub-workflow | `scenarioId`, `scenarioName` |
| `flow-control:router` | Route based on conditions | `routes` (array of conditions) |
| `flow-control:filter` | Filter data based on conditions | `conditions` |

**Configuration**:
- `scenarioId`: Sub-workflow ID
- `scenarioName`: Sub-workflow name
- `routes`: Array of routing conditions (for router)
- `conditions`: Filter conditions (for filter)

### Variable Modules

| Module Type | Business Logic Description | Key Fields |
|------------|---------------------------|------------|
| `tools:SetVariable` | Set a workflow variable | `name`, `value` |
| `tools:GetVariable` | Get a workflow variable | `name` |

**Configuration**:
- `name`: Variable name
- `value`: Variable value (for SetVariable)

### Async/Iteration Modules

| Module Type | Business Logic Description | Key Fields |
|------------|---------------------------|------------|
| `tools:Sleep` | Wait/Sleep for duration | `seconds` |
| `tools:Wait` | Wait for condition | `condition` |
| `tools:Repeater` | Repeat operation | `count`, `items` |

**Configuration**:
- `seconds`: Sleep duration in seconds
- `condition`: Wait condition
- `count`: Repeat count
- `items`: Items to iterate over

### Other Common Modules

| Module Type | Business Logic Description | Key Fields |
|------------|---------------------------|------------|
| `webhooks:customResponse` | Custom webhook response | `status`, `headers`, `body` |
| `text:aggregate` | Aggregate text | `items`, `separator` |
| `json:jsonParse` | Parse JSON | `json` |
| `json:jsonStringify` | Stringify JSON | `data` |

## Module Category Detection

The converter automatically categorizes modules:

- **`llm`**: OpenAI, OpenRouter modules
- **`database`**: Google Sheets, database modules
- **`http`**: HTTP request modules
- **`subscenario`**: StartSubscenario, CallSubscenario
- **`variable`**: SetVariable, GetVariable
- **`flow_control`**: Router, filter modules
- **`async`**: Sleep, wait modules
- **`iteration`**: Repeater modules
- **`other`**: All other module types

## Business Logic Mappings

The converter maps module types to human-readable descriptions:

- `openai-gpt-3:createModelResponse` → "LLM call using {model} - {name}"
- `google-sheets:getCell` → "Google Sheets getCell from {sheet}!{cell}"
- `http:request` → "HTTP {method} to {url}"
- `scenario-service:CallSubscenario` → "Call sub-workflow: {scenarioName}"

## Configuration Extraction

Each module type has specific configuration fields:

### LLM Modules
- Model name
- Input prompt (with mapper references)
- System prompt/instructions
- Max output tokens
- Tools configuration
- Background/async flag

### Database Modules
- Spreadsheet/sheet/cell references
- Operation type
- Value mappings

### HTTP Modules
- URL (with mapper references)
- HTTP method
- Headers and body

### Subscenarios
- Scenario ID/name
- Input parameters

