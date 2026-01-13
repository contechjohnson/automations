#!/usr/bin/env python3
"""
Make.com Blueprint Converter

Converts Make.com blueprint JSON files into human-readable business logic documentation
optimized for LLM analysis.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import defaultdict


def parse_blueprint(json_path: Path) -> Dict[str, Any]:
    """
    Load and parse a Make.com blueprint JSON file.
    
    Args:
        json_path: Path to the blueprint JSON file
        
    Returns:
        Dictionary containing parsed blueprint data with original path
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    flow = data.get("flow", [])
    blueprint_name = data.get("name", json_path.stem)
    
    # Parse all modules
    modules = []
    for module in flow:
        module_info = extract_module_logic(module)
        modules.append(module_info)
    
    # Build data flow graph
    data_flow = build_data_flow(flow)
    
    # Identify execution patterns
    patterns = identify_patterns(flow)
    
    return {
        "name": blueprint_name,
        "original_path": str(json_path.resolve()),
        "total_modules": len(flow),
        "modules": modules,
        "data_flow": data_flow,
        "patterns": patterns,
        "raw_data": data  # Keep for reference
    }


def extract_module_logic(module: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract business logic and configuration from a Make.com module.
    
    Args:
        module: Module dictionary from Make.com JSON
        
    Returns:
        Dictionary with extracted module information
    """
    module_id = module.get("id")
    module_type = module.get("module", "unknown")
    version = module.get("version", 1)
    
    # Get designer name
    designer_metadata = module.get("metadata", {}).get("designer", {})
    module_name = designer_metadata.get("name", f"Module {module_id}")
    
    # Extract mapper (data flow)
    mapper = module.get("mapper", {})
    
    # Extract parameters
    parameters = module.get("parameters", {})
    
    # Determine module category
    category = categorize_module(module_type)
    
    # Extract inputs from mapper references
    inputs = extract_inputs(mapper, module_id)
    
    # Extract configuration based on module type
    config = extract_configuration(module_type, mapper, parameters)
    
    # Extract LLM prompts if this is an LLM module
    prompts = {}
    if is_llm_module(module_type):
        prompts = extract_llm_prompts(mapper)
    
    return {
        "id": module_id,
        "name": module_name,
        "type": module_type,
        "category": category,
        "version": version,
        "inputs": inputs,
        "config": config,
        "mapper": mapper,
        "prompts": prompts,
        "purpose": describe_module_purpose(module_type, module_name, config)
    }


def categorize_module(module_type: str) -> str:
    """Categorize module by type."""
    if "openai" in module_type.lower() or "openrouter" in module_type.lower() or "gpt" in module_type.lower():
        return "llm"
    elif "google-sheets" in module_type:
        return "database"
    elif "http:" in module_type:
        return "http"
    elif "CallSubscenario" in module_type or "StartSubscenario" in module_type:
        return "subscenario"
    elif "SetVariable" in module_type or "GetVariable" in module_type:
        return "variable"
    elif "router" in module_type.lower() or "filter" in module_type.lower():
        return "flow_control"
    elif "sleep" in module_type.lower() or "wait" in module_type.lower():
        return "async"
    elif "repeater" in module_type.lower():
        return "iteration"
    else:
        return "other"


def is_llm_module(module_type: str) -> bool:
    """Check if module is an LLM/AI module."""
    return "openai" in module_type.lower() or "openrouter" in module_type.lower() or "gpt" in module_type.lower()


def extract_inputs(mapper: Dict[str, Any], current_module_id: int) -> List[Dict[str, str]]:
    """
    Extract input sources from mapper by finding references to other modules.
    
    Args:
        mapper: Mapper dictionary
        current_module_id: ID of current module
        
    Returns:
        List of input sources with module ID and field
    """
    inputs = []
    
    # Convert mapper to string to search for references
    mapper_str = json.dumps(mapper)
    
    # Pattern to match {{module_id.field}} or {{module_id}}
    pattern = r'\{\{(\d+)(?:\.(\w+))?\}\}'
    
    matches = re.findall(pattern, mapper_str)
    for match in matches:
        source_module_id = int(match[0])
        field = match[1] if match[1] else "output"
        
        # Don't include self-references
        if source_module_id != current_module_id:
            inputs.append({
                "module_id": source_module_id,
                "field": field
            })
    
    # Remove duplicates
    seen = set()
    unique_inputs = []
    for inp in inputs:
        key = (inp["module_id"], inp["field"])
        if key not in seen:
            seen.add(key)
            unique_inputs.append(inp)
    
    return unique_inputs


def extract_configuration(module_type: str, mapper: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Extract configuration details based on module type."""
    config = {}
    
    if "openai" in module_type.lower() or "gpt" in module_type.lower():
        config["model"] = mapper.get("model", "unknown")
        config["max_output_tokens"] = mapper.get("max_output_tokens")
        config["tools"] = mapper.get("tools", [])
        config["background"] = mapper.get("background", False)
        config["store"] = mapper.get("store", False)
        config["reasoning"] = mapper.get("reasoning", {})
    elif "google-sheets" in module_type:
        config["operation"] = module_type.split(":")[-1]
        config["sheet"] = mapper.get("sheetId", "")
        config["cell"] = mapper.get("cell", "")
        config["spreadsheet_id"] = mapper.get("spreadsheetId", "")
    elif "http:" in module_type:
        config["method"] = module_type.split(":")[-1]
        config["url"] = mapper.get("url", "")
    elif "CallSubscenario" in module_type or "StartSubscenario" in module_type:
        config["scenario_id"] = mapper.get("scenarioId", "")
        config["scenario_name"] = mapper.get("scenarioName", "")
    
    return config


def extract_llm_prompts(mapper: Dict[str, Any]) -> Dict[str, str]:
    """Extract system and user prompts from LLM module mapper."""
    prompts = {}
    
    # Instructions are typically the system prompt
    if "instructions" in mapper:
        prompts["system_prompt"] = mapper["instructions"]
    
    # Input is typically the user prompt
    if "input" in mapper:
        prompts["user_prompt"] = mapper["input"]
    
    return prompts


def describe_module_purpose(module_type: str, module_name: str, config: Dict[str, Any]) -> str:
    """Generate a human-readable description of what the module does."""
    if "openai" in module_type.lower() or "gpt" in module_type.lower():
        model = config.get("model", "unknown model")
        return f"LLM call using {model} - {module_name}"
    elif "google-sheets" in module_type:
        op = config.get("operation", "operation")
        sheet = config.get("sheet", "sheet")
        cell = config.get("cell", "cell")
        return f"Google Sheets {op} from {sheet}!{cell}"
    elif "http:" in module_type:
        method = config.get("method", "request").upper()
        url = config.get("url", "URL")
        return f"HTTP {method} to {url[:50]}..."
    elif "CallSubscenario" in module_type or "StartSubscenario" in module_type:
        scenario_name = config.get("scenario_name", "subscenario")
        return f"Call sub-workflow: {scenario_name}"
    elif "SetVariable" in module_type:
        return f"Set variable: {module_name}"
    elif "GetVariable" in module_type:
        return f"Get variable: {module_name}"
    else:
        return f"{module_type}: {module_name}"


def build_data_flow(flow: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build data flow graph by analyzing mapper references.
    
    Args:
        flow: List of modules from Make.com JSON
        
    Returns:
        Dictionary containing data flow information
    """
    # Build module lookup
    module_lookup = {module.get("id"): module for module in flow}
    
    # Track dependencies
    dependencies = defaultdict(list)  # target -> [sources]
    data_transformations = []
    
    for module in flow:
        module_id = module.get("id")
        mapper = module.get("mapper", {})
        mapper_str = json.dumps(mapper)
        
        # Find all input references
        pattern = r'\{\{(\d+)(?:\.(\w+))?\}\}'
        matches = re.findall(pattern, mapper_str)
        
        for match in matches:
            source_module_id = int(match[0])
            field = match[1] if match[1] else "output"
            
            if source_module_id != module_id and source_module_id in module_lookup:
                dependencies[module_id].append({
                    "source_module_id": source_module_id,
                    "field": field
                })
                
                # Record transformation
                source_module = module_lookup[source_module_id]
                source_name = source_module.get("metadata", {}).get("designer", {}).get("name", f"Module {source_module_id}")
                target_name = module.get("metadata", {}).get("designer", {}).get("name", f"Module {module_id}")
                
                data_transformations.append({
                    "from": {
                        "id": source_module_id,
                        "name": source_name,
                        "field": field
                    },
                    "to": {
                        "id": module_id,
                        "name": target_name
                    }
                })
    
    # Find unused outputs (modules whose output is never referenced)
    all_source_ids = set()
    for deps in dependencies.values():
        for dep in deps:
            all_source_ids.add(dep["source_module_id"])
    
    used_module_ids = set(dependencies.keys()) | all_source_ids
    
    # Find potential data loss points (modules with no outputs used)
    potential_data_loss = []
    for module in flow:
        module_id = module.get("id")
        if module_id not in used_module_ids and module_id not in [1]:  # Exclude trigger modules
            module_name = module.get("metadata", {}).get("designer", {}).get("name", f"Module {module_id}")
            potential_data_loss.append({
                "module_id": module_id,
                "name": module_name
            })
    
    return {
        "dependencies": dict(dependencies),
        "transformations": data_transformations,
        "potential_data_loss": potential_data_loss
    }


def identify_patterns(flow: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Identify execution patterns in the workflow.
    
    Args:
        flow: List of modules from Make.com JSON
        
    Returns:
        Dictionary containing identified patterns
    """
    patterns = {
        "execution_type": "sequential",  # sequential, parallel, async, mixed
        "has_subscenarios": False,
        "has_async_operations": False,
        "has_iteration": False,
        "has_flow_control": False,
        "error_handling": [],
        "parallel_opportunities": [],
        "bottlenecks": []
    }
    
    # Build dependency graph
    dependencies = defaultdict(list)
    for module in flow:
        module_id = module.get("id")
        mapper = module.get("mapper", {})
        mapper_str = json.dumps(mapper)
        
        pattern = r'\{\{(\d+)(?:\.(\w+))?\}\}'
        matches = re.findall(pattern, mapper_str)
        
        for match in matches:
            source_module_id = int(match[0])
            if source_module_id != module_id:
                dependencies[module_id].append(source_module_id)
    
    # Check for subscenarios
    for module in flow:
        module_type = module.get("module", "")
        if "CallSubscenario" in module_type or "StartSubscenario" in module_type:
            patterns["has_subscenarios"] = True
    
    # Check for async operations
    for module in flow:
        module_type = module.get("module", "").lower()
        if "sleep" in module_type or "wait" in module_type:
            patterns["has_async_operations"] = True
        if "repeater" in module_type:
            patterns["has_iteration"] = True
        if "router" in module_type or "filter" in module_type:
            patterns["has_flow_control"] = True
    
    # Determine execution type
    if patterns["has_async_operations"]:
        patterns["execution_type"] = "async"
    elif patterns["has_subscenarios"]:
        # Subscenarios can run in parallel
        subscenario_count = sum(1 for m in flow if "CallSubscenario" in m.get("module", ""))
        if subscenario_count > 1:
            patterns["execution_type"] = "parallel"
        else:
            patterns["execution_type"] = "mixed"
    
    # Find parallel opportunities (modules that don't depend on each other)
    independent_modules = []
    for module in flow:
        module_id = module.get("id")
        if module_id not in dependencies:
            module_name = module.get("metadata", {}).get("designer", {}).get("name", f"Module {module_id}")
            independent_modules.append({
                "id": module_id,
                "name": module_name
            })
    
    if len(independent_modules) > 1:
        patterns["parallel_opportunities"] = independent_modules
    
    # Identify bottlenecks (modules with many dependents)
    dependent_count = defaultdict(int)
    for deps in dependencies.values():
        for dep in deps:
            dependent_count[dep] += 1
    
    bottlenecks = []
    for module_id, count in dependent_count.items():
        if count > 3:  # More than 3 modules depend on this
            module = next((m for m in flow if m.get("id") == module_id), None)
            if module:
                module_name = module.get("metadata", {}).get("designer", {}).get("name", f"Module {module_id}")
                bottlenecks.append({
                    "id": module_id,
                    "name": module_name,
                    "dependent_count": count
                })
    
    patterns["bottlenecks"] = bottlenecks
    
    return patterns


def generate_business_logic_report(
    blueprint_data: Dict[str, Any],
    use_llm: bool = False,
    llm_model: str = "gpt-4.1"
) -> str:
    """
    Generate human-readable markdown report from parsed blueprint data.
    
    Args:
        blueprint_data: Parsed blueprint data from parse_blueprint()
        use_llm: Whether to use LLM enhancement (optional)
        llm_model: LLM model to use for enhancement
        
    Returns:
        Markdown string with business logic report
    """
    name = blueprint_data["name"]
    original_path = blueprint_data["original_path"]
    modules = blueprint_data["modules"]
    data_flow = blueprint_data["data_flow"]
    patterns = blueprint_data["patterns"]
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Count module types
    llm_count = sum(1 for m in modules if m["category"] == "llm")
    db_count = sum(1 for m in modules if m["category"] == "database")
    subscenario_count = sum(1 for m in modules if m["category"] == "subscenario")
    
    # Generate markdown
    report = f"""# Workflow: {name}

## Overview
- **Purpose**: Make.com workflow blueprint
- **Total Modules**: {len(modules)}
- **Execution Pattern**: {patterns['execution_type'].title()}
- **LLM/AI Modules**: {llm_count}
- **Database Operations**: {db_count}
- **Subscenarios**: {subscenario_count}
- **Analysis Timestamp**: {timestamp}
- **Original JSON**: `{original_path}`

## Execution Flow

"""
    
    # Add each module as a step
    for i, module in enumerate(modules, 1):
        report += f"""### Step {i}: {module['name']} (ID: {module['id']})

- **Type**: {module['type']}
- **Category**: {module['category']}
- **Purpose**: {module['purpose']}
"""
        
        if module['inputs']:
            report += "- **Inputs**:\n"
            for inp in module['inputs']:
                report += f"  - From Module {inp['module_id']}: `{inp['field']}`\n"
        
        if module['config']:
            report += "- **Configuration**:\n"
            for key, value in module['config'].items():
                if value:  # Only show non-empty config
                    if isinstance(value, (list, dict)):
                        value_str = json.dumps(value, indent=2)[:200]  # Truncate long values
                        if len(json.dumps(value)) > 200:
                            value_str += "..."
                        report += f"  - {key}: {value_str}\n"
                    else:
                        report += f"  - {key}: {value}\n"
        
        # Add prompts if this is an LLM module
        if module['prompts']:
            if 'system_prompt' in module['prompts']:
                system_prompt = module['prompts']['system_prompt']
                # Replace mapper references for readability
                system_prompt = re.sub(r'\{\{(\d+)(?:\.(\w+))?\}\}', r'[Module \1.\2]', system_prompt)
                report += f"- **System Prompt**:\n```\n{system_prompt[:500]}{'...' if len(system_prompt) > 500 else ''}\n```\n"
            if 'user_prompt' in module['prompts']:
                user_prompt = module['prompts']['user_prompt']
                user_prompt = re.sub(r'\{\{(\d+)(?:\.(\w+))?\}\}', r'[Module \1.\2]', user_prompt)
                report += f"- **User Prompt**:\n```\n{user_prompt[:500]}{'...' if len(user_prompt) > 500 else ''}\n```\n"
        
        report += "\n"
    
    # Data flow diagram
    report += """## Data Flow Diagram

"""
    
    if data_flow['transformations']:
        report += "Data transformations:\n\n"
        for trans in data_flow['transformations'][:20]:  # Limit to first 20
            from_module = trans['from']
            to_module = trans['to']
            report += f"- Module {from_module['id']} ({from_module['name']}) → Module {to_module['id']} ({to_module['name']}) via `{from_module['field']}`\n"
        
        if len(data_flow['transformations']) > 20:
            report += f"- ... and {len(data_flow['transformations']) - 20} more transformations\n"
        report += "\n"
    else:
        report += "No explicit data transformations detected.\n\n"
    
    # Module relationships
    report += """## Module Relationships

"""
    
    if data_flow['dependencies']:
        for target_id, sources in list(data_flow['dependencies'].items())[:20]:
            target_module = next((m for m in modules if m['id'] == target_id), None)
            if target_module:
                target_name = target_module['name']
                source_names = []
                for source in sources:
                    source_module = next((m for m in modules if m['id'] == source['source_module_id']), None)
                    if source_module:
                        source_names.append(f"Module {source['source_module_id']} ({source_module['name']}) via `{source['field']}`")
                
                if source_names:
                    report += f"- Module {target_id} ({target_name}) depends on: {', '.join(source_names)}\n"
        
        if len(data_flow['dependencies']) > 20:
            report += f"- ... and {len(data_flow['dependencies']) - 20} more relationships\n"
        report += "\n"
    
    # LLM Prompts Extracted
    all_system_prompts = []
    all_user_prompts = []
    
    for module in modules:
        if module['prompts']:
            if 'system_prompt' in module['prompts']:
                all_system_prompts.append({
                    "module": module['name'],
                    "prompt": module['prompts']['system_prompt']
                })
            if 'user_prompt' in module['prompts']:
                all_user_prompts.append({
                    "module": module['name'],
                    "prompt": module['prompts']['user_prompt']
                })
    
    if all_system_prompts or all_user_prompts:
        report += """## LLM Prompts Extracted

"""
        if all_system_prompts:
            report += "- **System Prompts**:\n"
            for prompt_info in all_system_prompts:
                report += f"  - {prompt_info['module']}:\n    ```\n    {prompt_info['prompt'][:300]}...\n    ```\n"
        
        if all_user_prompts:
            report += "- **User Prompts**:\n"
            for prompt_info in all_user_prompts:
                report += f"  - {prompt_info['module']}:\n    ```\n    {prompt_info['prompt'][:300]}...\n    ```\n"
        
        report += "\n"
    
    # Potential Issues
    issues = []
    
    # Data loss
    if data_flow['potential_data_loss']:
        for loss in data_flow['potential_data_loss']:
            issues.append(f"Potential data loss: Module {loss['module_id']} ({loss['name']}) output may not be used")
    
    # Missing error handlers
    has_http = any(m['category'] == 'http' for m in modules)
    has_db = any(m['category'] == 'database' for m in modules)
    if (has_http or has_db) and not patterns['has_flow_control']:
        issues.append("No explicit error handling detected for external API/database calls")
    
    if issues:
        report += """## Potential Issues

"""
        for issue in issues:
            report += f"- {issue}\n"
        report += "\n"
    
    # Efficiency Analysis
    report += """## Efficiency Analysis

"""
    
    if patterns['bottlenecks']:
        report += "- **Bottlenecks**:\n"
        for bottleneck in patterns['bottlenecks']:
            report += f"  - Module {bottleneck['id']} ({bottleneck['name']}): {bottleneck['dependent_count']} modules depend on this\n"
        report += "\n"
    
    if patterns['parallel_opportunities']:
        report += "- **Parallel Opportunities**:\n"
        for opp in patterns['parallel_opportunities'][:5]:
            report += f"  - Module {opp['id']} ({opp['name']}) could potentially run in parallel\n"
        report += "\n"
    
    # Check for redundant operations
    redundant = detect_redundant_operations(modules)
    if redundant:
        report += "- **Redundant Operations**:\n"
        for red in redundant[:5]:
            report += f"  - {red}\n"
        report += "\n"
    
    # Reference Documentation
    report += """## Reference Documentation

- **Make.com JSON Structure**: See `.claude/skills/parsing-make-blueprints/reference/MAKE_COM_JSON_STRUCTURE.md`
- **Module Types**: See `.claude/skills/parsing-make-blueprints/reference/MODULE_TYPES.md`
- **Mapper Syntax**: See `.claude/skills/parsing-make-blueprints/reference/MAPPER_SYNTAX.md`
- **Original JSON**: `{original_path}`

"""
    
    # LLM enhancement
    if use_llm:
        enhanced_report = enhance_with_llm(blueprint_data, llm_model)
        if enhanced_report:
            report += f"\n---\n\n## LLM-Enhanced Analysis\n\n{enhanced_report}\n"
    
    return report


def enhance_with_llm(blueprint_data: Dict[str, Any], model: str = "gpt-4.1") -> Optional[str]:
    """
    Enhance the report with LLM analysis.
    
    Args:
        blueprint_data: Parsed blueprint data
        model: LLM model to use
        
    Returns:
        Enhanced markdown string or None if enhancement fails
    """
    try:
        # Import workers.ai if available
        import sys
        from pathlib import Path
        
        # Add workers directory to path
        workers_path = Path(__file__).parent.parent.parent.parent / "workers"
        if workers_path.exists():
            sys.path.insert(0, str(workers_path.parent))
            try:
                from workers.ai import ai
            except ImportError:
                # Fallback to direct OpenAI
                import os
                from openai import OpenAI
                openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                def ai(prompt: str, model: str = "gpt-4.1", system: str = None):
                    messages = []
                    if system:
                        messages.append({"role": "system", "content": system})
                    messages.append({"role": "user", "content": prompt})
                    response = openai_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.7,
                    )
                    return response.choices[0].message.content
        else:
            # Fallback to direct OpenAI
            import os
            from openai import OpenAI
            if not os.environ.get("OPENAI_API_KEY"):
                return None
            openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            def ai(prompt: str, model: str = "gpt-4.1", system: str = None):
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                response = openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                )
                return response.choices[0].message.content
        
        # Simplify blueprint data for token efficiency
        simplified = simplify_blueprint_for_llm(blueprint_data)
        
        # Build prompt for LLM
        system_prompt = """You are an expert at analyzing Make.com workflows and identifying business logic, inefficiencies, and potential improvements. Analyze the workflow and provide insights."""
        
        user_prompt = f"""Analyze this Make.com workflow and provide:

1. A concise business logic summary
2. Key execution patterns identified
3. Potential inefficiencies or bottlenecks
4. Recommendations for improvement

Workflow: {blueprint_data['name']}
Total Modules: {blueprint_data['total_modules']}
Execution Pattern: {blueprint_data['patterns']['execution_type']}

Simplified workflow structure:
{json.dumps(simplified, indent=2)[:8000]}  # Limit to ~8k chars

Provide a concise analysis focusing on business logic and efficiency."""
        
        # Try primary model, fallback to cheaper model
        try:
            enhanced = ai(user_prompt, model=model, system=system_prompt)
        except Exception:
            # Fallback to gpt-4.1-mini or gpt-3.5-turbo
            fallback_model = "gpt-4.1-mini" if model != "gpt-4.1-mini" else "gpt-3.5-turbo"
            enhanced = ai(user_prompt, model=fallback_model, system=system_prompt)
        
        return enhanced
        
    except Exception as e:
        # Silently fail if LLM enhancement not available
        return None


def simplify_blueprint_for_llm(blueprint_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplify blueprint data for token efficiency.
    Keep only essential information for LLM analysis.
    """
    simplified_modules = []
    
    for module in blueprint_data['modules'][:30]:  # Limit to first 30 modules
        simplified = {
            "id": module['id'],
            "name": module['name'],
            "type": module['type'],
            "category": module['category'],
            "purpose": module['purpose'],
        }
        
        # Only include key config
        if module['config']:
            key_config = {}
            for key in ['model', 'operation', 'method', 'url', 'sheet', 'cell']:
                if key in module['config'] and module['config'][key]:
                    key_config[key] = module['config'][key]
            if key_config:
                simplified['config'] = key_config
        
        # Truncate prompts if present
        if module['prompts']:
            simplified_prompts = {}
            for key, value in module['prompts'].items():
                if value:
                    simplified_prompts[key] = value[:200] + "..." if len(value) > 200 else value
            if simplified_prompts:
                simplified['prompts'] = simplified_prompts
        
        simplified_modules.append(simplified)
    
    return {
        "name": blueprint_data['name'],
        "total_modules": blueprint_data['total_modules'],
        "modules": simplified_modules,
        "execution_type": blueprint_data['patterns']['execution_type'],
        "has_subscenarios": blueprint_data['patterns']['has_subscenarios'],
        "has_async": blueprint_data['patterns']['has_async_operations'],
    }


def detect_redundant_operations(modules: List[Dict[str, Any]]) -> List[str]:
    """Detect potentially redundant operations."""
    redundant = []
    
    # Group modules by type and config
    module_groups = defaultdict(list)
    for module in modules:
        key = (module['type'], json.dumps(module['config'], sort_keys=True))
        module_groups[key].append(module)
    
    # Find duplicates
    for key, group in module_groups.items():
        if len(group) > 1:
            module_type = group[0]['type']
            redundant.append(f"Multiple {module_type} modules with same config: {', '.join([m['name'] for m in group])}")
    
    return redundant


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert Make.com blueprint JSON to business logic markdown")
    parser.add_argument("--input", type=Path, help="Path to Make.com JSON file (required unless using --batch)")
    parser.add_argument("--output", type=Path, help="Output file path (default: stdout)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--analysis", choices=["basic", "full", "minimal"], default="full", help="Analysis depth")
    parser.add_argument("--llm-enhance", action="store_true", help="Use LLM to enhance the summary")
    parser.add_argument("--llm-model", default="gpt-4.1", help="LLM model to use for enhancement")
    parser.add_argument("--batch", type=Path, help="Process all JSON files in a directory")
    parser.add_argument("--include-original-path", action="store_true", default=True, help="Include original JSON path in output")

    args = parser.parse_args()

    # Validate that either --input or --batch is provided
    if not args.batch and not args.input:
        parser.error("Either --input or --batch must be provided")
    
    if args.batch:
        # Batch processing
        json_files = list(args.batch.glob("*.json")) + list(args.batch.glob("*.blueprint.json"))
        for json_file in json_files:
            print(f"Processing {json_file.name}...")
            blueprint_data = parse_blueprint(json_file)
            report = generate_business_logic_report(
                blueprint_data,
                use_llm=args.llm_enhance,
                llm_model=args.llm_model
            )
            
            output_file = args.output / f"{json_file.stem}_business_logic.md" if args.output else None
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w') as f:
                    f.write(report)
                print(f"  → {output_file}")
            else:
                print(report)
    else:
        # Single file processing
        blueprint_data = parse_blueprint(args.input)
        
        if args.format == "json":
            output = json.dumps(blueprint_data, indent=2)
        else:
            output = generate_business_logic_report(
                blueprint_data,
                use_llm=args.llm_enhance,
                llm_model=args.llm_model
            )
        
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Output written to {args.output}")
        else:
            print(output)

