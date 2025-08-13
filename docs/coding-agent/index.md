# Coding Agent Integration

This section documents the integration with AI coding agents like Claude Code and the associated tooling configurations.

## Overview

This repository is designed to work seamlessly with AI coding agents, particularly Claude Code, to enable:

- **Automated Documentation**: Generate and maintain documentation from code
- **Visual Testing**: Take screenshots and validate documentation rendering
- **Task Automation**: Execute complex workflows through natural language commands
- **Development Workflows**: Streamline common development tasks

## Model Context Protocol (MCP) Servers

The project uses Model Context Protocol (MCP) servers to extend AI agent capabilities with specialized tools.

### Configuration

MCP servers are configured via a `.mcp.json` file in the project root, which enables:

- **Project-scoped servers**: Available only when working within this project
- **Version control integration**: Configuration can be committed and shared with team
- **Automatic setup**: New developers get the same tooling automatically

### Current MCP Servers

The following MCP servers are configured for this project:

#### Playwright MCP
**Purpose**: Web browser automation and screenshot capabilities  
**Use cases**:
- Taking screenshots of documentation for visual review
- Testing documentation rendering across different browsers
- Automated navigation and validation of docs structure
- Identifying layout and styling issues

**Configuration** (`.mcp.json`):
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {}
    }
  }
}
```

**Usage Examples**:
- "Use playwright to navigate to http://localhost:8000 and take screenshots of all documentation pages"
- "Check the documentation layout on different screen sizes"
- "Validate that all navigation links work correctly"

### Prerequisites

To use MCP servers with Claude Code:

1. **Node.js 18+**: Required for running npm/npx-based MCP servers
2. **Claude Code CLI**: Install and configure Claude Code
3. **Project Setup**: Ensure you're in the project directory when starting Claude

### Getting Started

1. **Start Documentation Server**:
   ```bash
   mise run serve-docs
   ```

2. **Launch Claude Code**:
   ```bash
   claude
   ```

3. **First-time Setup**:
   - Claude will detect the `.mcp.json` configuration
   - You'll be prompted to approve MCP servers on first use
   - Accept the Playwright MCP server when prompted

4. **Test Integration**:
   ```
   Use playwright to open a browser and navigate to http://localhost:8000
   ```

### Security Considerations

- **User Approval Required**: MCP servers require explicit user approval before first use
- **Project-scoped**: Servers are only available within this project directory  
- **Transparent Configuration**: All server configurations are visible in `.mcp.json`
- **Reset Capabilities**: Use `claude mcp reset-project-choices` to reset approvals

### Management Commands

- **List configured servers**: `claude mcp list`
- **Reset approval choices**: `claude mcp reset-project-choices`
- **View available tools**: Use `/mcp` command in Claude Code

### Common Workflows

#### Documentation Visual Review
1. Start the docs server: `mise run serve-docs`
2. Ask Claude to navigate through documentation sections
3. Take screenshots of each page to review layout and formatting
4. Identify and fix any rendering issues

#### Cross-Browser Testing
1. Use Playwright to test documentation in different browsers (Chromium, Firefox, WebKit)
2. Capture screenshots from each browser for comparison
3. Ensure consistent rendering across platforms

#### Accessibility Validation
1. Use Playwright's accessibility tree analysis
2. Identify navigation and usability issues
3. Validate that documentation is accessible to all users

## Benefits for Development

### Enhanced Debugging
- **Visual Feedback**: See exactly how changes affect documentation rendering
- **Interactive Testing**: Navigate and test documentation like a real user
- **Automated Validation**: Run comprehensive tests with simple natural language commands

### Improved Collaboration
- **Shared Configuration**: Team members get identical tooling setup
- **Documentation Screenshots**: Visual evidence of issues for better communication
- **Consistent Environment**: Same tools available to all developers

### Streamlined Workflows
- **Natural Language Interface**: Complex browser automation through simple commands
- **Integrated Testing**: Test documentation without leaving the development environment
- **Automated Tasks**: Combine multiple operations into single requests