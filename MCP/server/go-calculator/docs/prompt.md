Create an MCP server that
    exposes tool to perform below operations
        addition
        subtraction
        multiplication
        division
    uses streamable http transport
    uses go language
    is performant
    follows best practices in
        logging
        error handling
        performant system design
        configuration management


<!-- gave above prompt to duck.ai and asked it to refine it further based on other go lang standards to get to below prompt -->
Create an MCP server in Go that:
    Exposes tools for the following mathematical operations:
        Addition
        Subtraction
        Multiplication
        Division
    Utilizes streamable HTTP transport to support real-time communication.
    Ensures high performance by implementing efficient algorithms and data structures.
    Follows Go best practices in:
        Logging: Implement structured and leveled logging for better traceability and debugging.
        Error Handling: Utilize idiomatic error handling to manage errors gracefully and provide meaningful user feedback.
        System Design: Adopt a modular architecture with clear separation of concerns (e.g., routing, business logic, and data access).
        Configuration Management: Use environment variables or configuration files to manage settings securely, ensuring sensitive data is handled properly.
        Testing: Incorporate unit tests and integration tests for better reliability and validation of functionality.
        Code Organization: Adhere to a standard project layout, separating packages for handlers, models, and utilities.
        Concurrency: Leverage goroutines and channels to manage concurrent requests efficiently.
        Security: Validate user inputs to prevent injection attacks and ensure data integrity.
        Graceful Shutdown: Implement signal handling to ensure graceful shutdown, allowing for completion of ongoing requests.
        Performance Monitoring: Integrate monitoring tools to assess application performance and identify potential bottlenecks.
        Dependency Management: Utilize Go modules to manage dependencies effectively and keep them updated.
        API Versioning: Implement versioning in your HTTP API to accommodate future changes.
        Context Usage: Use context for request cancellation, timeouts, and passing request-scoped values across API boundaries.

<!-- gave it permission to perform all edits and generate the project structure and files -->

<!-- Prompt to include ObsMon in implementation -->
    refer to the current golang project and documentation at
    https://arize.com/docs/phoenix to prepare a plan on how we can implement
    observability and monitoring consistently across all tools irrespective of the       
    language used for it e.g. if the language is python as in
    D:\AI\MCP\server\py-calculator