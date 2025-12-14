"""Calculator operations interface and implementations following SOLID principles."""
from abc import ABC, abstractmethod
from typing import Union, Dict, Any

Number = Union[int, float]

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
        """Perform the specified calculation."""
        if operation not in self._operations:
            raise ValueError(f"Unknown operation: {operation}")
        
        return self._operations[operation].execute(a, b)