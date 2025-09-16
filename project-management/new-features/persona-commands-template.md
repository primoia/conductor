# Command Template for Agent Personas

## Section to be Included in All Personas

### Available Commands

#### Help Command
**Accepted commands:**
- `help`
- `ajuda`
- `comandos`
- `?`

**Action:**
Display this list of available commands:

```
🤖 **AVAILABLE COMMANDS:**

📋 **PREVIEW (without saving):**
• preview
• preview document
• show document

💾 **GENERATE/SAVE (with versioning):**
• generate document
• create artifact
• save document
• execute task
• consolidate

❓ **HELP:**
• help / ajuda / comandos / ?

📊 **HOW TO USE:**
1. Discuss the [problem/requirement/code] with me
2. Use "preview" to see what the document would look like
3. Use "generate document" to save (v1.0, v1.1, v1.2...)
4. Continue chatting for incremental refinements

📁 **CONFIGURED OUTPUT:**
• File: [output_artifact from agent.yaml]
• Directory: [output_directory from agent.yaml]
```

#### Preview Command
**Accepted commands:**
- `preview`
- `preview document`  
- `show document`

**Action:**
1. Use **Read** to load `state.json`
2. Generate the full document content based on the history
3. **DO NOT save the file** - only display the content in the chat
4. Start the response with: "📋 **PREVIEW of the output document:**"

#### Generation/Merge Command (Incremental)
**Accepted commands:**
- `generate document`
- `create artifact`
- `save document`
- `execute task`
- `consolidate`

**Action:**
1. Use **Read** to load `state.json`
2. **Determine output configuration**: File name and directory according to the agent's configuration
3. **Check if document already exists**: Use **Read** on the full path

**If document does NOT exist:**
- Create a new document based on the full history
- Version: v1.0

**If document ALREADY exists:**
- **INCREMENTAL MERGE**: Combine the existing document + new conversations
- **Versioning**: Increment the version (v1.0 → v1.1, v1.1 → v1.2, etc.)
- **Preserve previous context** + add new analysis
- **Mark updated sections** with a timestamp

4. **CREATE the folder structure if necessary**: according to the agent's configuration
5. Use **Write** to save the updated document to the configured path

#### Dynamic Configuration
**The output file name and directory are configurable:**
- **File**: Defined in `output_artifact` in agent.yaml
- **Directory**: Defined in `output_directory` in agent.yaml
- **For this agent**: `{output_artifact}` in `{output_directory}/`

**SPECIFIC AUTHORIZATION**: You have FULL permission to:
- Create folders according to the agent's configuration
- Read existing documents for merging
- Write configured output files
- Execute without asking for permission!

## Customization by Agent Type

### For Problem Refiners:
```
1. Discuss the problem with me
```

### For Code Generators:
```
1. Discuss the code requirements with me
```

### For Test Creators:
```
1. Discuss the test scenarios with me
```

### For Documentation Agents:
```
1. Discuss the required documentation with me
```

## How to Integrate

1. **Copy the "Available Commands" section** to your persona.md
2. **Adjust the "Discuss the [problem/requirement/code]" line** according to the agent type
3. **Configure output_artifact and output_directory** in agent.yaml
4. **Test the** help, preview, and generate document commands

## Benefits

- ✅ **Standardization**: All agents have the same commands
- ✅ **Self-documentation**: Help embedded in the chat
- ✅ **Clear Workflow**: Preview → generate → refine → consolidate
- ✅ **Versioning**: Automatic incremental merging
- ✅ **Scalability**: Easy creation of new agents