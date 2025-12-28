"""Calculator operations interface and implementations following SOLID principles."""
from abc import ABC, abstractmethod
from typing import Union, Dict, Any
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

Number = Union[int, float]

# Get tracer instance
tracer = trace.get_tracer("py-calculator")

class Operation(ABC):
    """Abstract base class for calculator operations."""
    
    @abstractmethod
    def execute(self, a: Number, b: Number) -> Number:
        """Execute the operation on two numbers."""
        pass

class Addition(Operation):
    """Addition operation implementation."""
    
    def execute(self, a: Number, b: Number) -> Number:
        return a + b

class Subtraction(Operation):
    """Subtraction operation implementation."""
    
    def execute(self, a: Number, b: Number) -> Number:
        return a - b

class Multiplication(Operation):
    """Multiplication operation implementation."""
    
    def execute(self, a: Number, b: Number) -> Number:
        return a * b

class Division(Operation):
    """Division operation implementation."""
    
    def execute(self, a: Number, b: Number) -> Number:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

class Calculator:
    """Calculator class that manages operations."""

    def __init__(self):
        self._operations: Dict[str, Operation] = {
            'add': Addition(),
            'subtract': Subtraction(),
            'multiply': Multiplication(),
            'divide': Division()
        }

    def calculate(self, operation: str, a: Number, b: Number) -> Number:
        """Perform the specified calculation with tracing."""
        with tracer.start_as_current_span("calculator.calculate") as span:
            span.set_attribute("mcp.method", "tools/call")
            span.set_attribute("mcp.tool.name", operation)
            span.set_attribute("mcp.tool.arg.a", float(a))
            span.set_attribute("mcp.tool.arg.b", float(b))

            if operation not in self._operations:
                span.set_status(Status(StatusCode.ERROR))
                error = ValueError(f"Unknown operation: {operation}")
                span.record_exception(error)
                span.set_attribute("mcp.tool.error", True)
                raise error

            try:
                result = self._operations[operation].execute(a, b)
                span.set_attribute("mcp.tool.result", float(result))
                span.set_attribute("mcp.tool.error", False)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR))
                span.record_exception(e)
                span.set_attribute("mcp.tool.error", True)
                raise