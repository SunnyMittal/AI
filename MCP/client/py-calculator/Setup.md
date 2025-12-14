Create a python based MCP web Client for calculator MCP server at D:\AI\MCP\server\calculator such that it
- uses ollama based local llm model llama3.1:8b model
- has a chat interface where user is able to provide input
- can pass user input to llm to determine which tool to execute on the mcp server
- can call the right MCP tools
- is performant and maintainable
- follows SOLID design principles

Install dependencies
>pip install -r requirements.txt

Start the application
>uvicorn app.main:app --reload

generate a prompt to be able to generate such a client for consuming MCP servers again deterministically and accurately
    write the document to /docs/regen.md file