package calculator

import (
	"errors"
	"math"
)

var (
	// ErrDivisionByZero is returned when attempting to divide by zero
	ErrDivisionByZero = errors.New("division by zero is not allowed")
	// ErrInvalidOperation is returned for invalid operations
	ErrInvalidOperation = errors.New("invalid operation")
)

// Calculator provides mathematical operations
type Calculator struct{}

// New creates a new Calculator instance
func New() *Calculator {
	return &Calculator{}
}

// Add performs addition of two numbers
func (c *Calculator) Add(a, b float64) float64 {
	return a + b
}

// Subtract performs subtraction of two numbers
func (c *Calculator) Subtract(a, b float64) float64 {
	return a - b
}

// Multiply performs multiplication of two numbers
func (c *Calculator) Multiply(a, b float64) float64 {
	return a * b
}

// Divide performs division of two numbers
// Returns an error if the divisor is zero
func (c *Calculator) Divide(a, b float64) (float64, error) {
	if b == 0 {
		return 0, ErrDivisionByZero
	}

	result := a / b

	// Check for infinity or NaN
	if math.IsInf(result, 0) || math.IsNaN(result) {
		return 0, ErrInvalidOperation
	}

	return result, nil
}

// ValidateNumbers checks if the provided numbers are valid (not NaN or Inf)
func ValidateNumbers(numbers ...float64) error {
	for _, num := range numbers {
		if math.IsNaN(num) {
			return errors.New("input contains NaN (Not a Number)")
		}
		if math.IsInf(num, 0) {
			return errors.New("input contains infinity")
		}
	}
	return nil
}
