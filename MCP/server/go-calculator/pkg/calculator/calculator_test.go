package calculator

import (
	"math"
	"testing"
)

func TestCalculator_Add(t *testing.T) {
	calc := New()

	tests := []struct {
		name     string
		a, b     float64
		expected float64
	}{
		{"positive numbers", 5, 3, 8},
		{"negative numbers", -5, -3, -8},
		{"mixed signs", 5, -3, 2},
		{"with zero", 5, 0, 5},
		{"decimals", 2.5, 3.7, 6.2},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Add(tt.a, tt.b)
			if math.Abs(result-tt.expected) > 1e-10 {
				t.Errorf("Add(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
			}
		})
	}
}

func TestCalculator_Subtract(t *testing.T) {
	calc := New()

	tests := []struct {
		name     string
		a, b     float64
		expected float64
	}{
		{"positive numbers", 5, 3, 2},
		{"negative numbers", -5, -3, -2},
		{"mixed signs", 5, -3, 8},
		{"with zero", 5, 0, 5},
		{"decimals", 5.7, 2.5, 3.2},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Subtract(tt.a, tt.b)
			if math.Abs(result-tt.expected) > 1e-10 {
				t.Errorf("Subtract(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
			}
		})
	}
}

func TestCalculator_Multiply(t *testing.T) {
	calc := New()

	tests := []struct {
		name     string
		a, b     float64
		expected float64
	}{
		{"positive numbers", 5, 3, 15},
		{"negative numbers", -5, -3, 15},
		{"mixed signs", 5, -3, -15},
		{"with zero", 5, 0, 0},
		{"decimals", 2.5, 4, 10},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := calc.Multiply(tt.a, tt.b)
			if math.Abs(result-tt.expected) > 1e-10 {
				t.Errorf("Multiply(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
			}
		})
	}
}

func TestCalculator_Divide(t *testing.T) {
	calc := New()

	tests := []struct {
		name      string
		a, b      float64
		expected  float64
		expectErr bool
	}{
		{"positive numbers", 6, 3, 2, false},
		{"negative numbers", -6, -3, 2, false},
		{"mixed signs", 6, -3, -2, false},
		{"division by zero", 5, 0, 0, true},
		{"decimals", 7.5, 2.5, 3, false},
		{"zero divided by number", 0, 5, 0, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := calc.Divide(tt.a, tt.b)

			if tt.expectErr {
				if err == nil {
					t.Errorf("Divide(%f, %f) expected error, got nil", tt.a, tt.b)
				}
				if err != ErrDivisionByZero {
					t.Errorf("Divide(%f, %f) expected ErrDivisionByZero, got %v", tt.a, tt.b, err)
				}
			} else {
				if err != nil {
					t.Errorf("Divide(%f, %f) unexpected error: %v", tt.a, tt.b, err)
				}
				if math.Abs(result-tt.expected) > 1e-10 {
					t.Errorf("Divide(%f, %f) = %f; want %f", tt.a, tt.b, result, tt.expected)
				}
			}
		})
	}
}

func TestValidateNumbers(t *testing.T) {
	tests := []struct {
		name      string
		numbers   []float64
		expectErr bool
	}{
		{"valid numbers", []float64{1, 2, 3}, false},
		{"with NaN", []float64{1, math.NaN(), 3}, true},
		{"with positive infinity", []float64{1, math.Inf(1), 3}, true},
		{"with negative infinity", []float64{1, math.Inf(-1), 3}, true},
		{"empty slice", []float64{}, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateNumbers(tt.numbers...)
			if tt.expectErr && err == nil {
				t.Error("ValidateNumbers expected error, got nil")
			}
			if !tt.expectErr && err != nil {
				t.Errorf("ValidateNumbers unexpected error: %v", err)
			}
		})
	}
}

// Benchmark tests
func BenchmarkAdd(b *testing.B) {
	calc := New()
	for i := 0; i < b.N; i++ {
		calc.Add(12345.6789, 98765.4321)
	}
}

func BenchmarkSubtract(b *testing.B) {
	calc := New()
	for i := 0; i < b.N; i++ {
		calc.Subtract(12345.6789, 98765.4321)
	}
}

func BenchmarkMultiply(b *testing.B) {
	calc := New()
	for i := 0; i < b.N; i++ {
		calc.Multiply(12345.6789, 98765.4321)
	}
}

func BenchmarkDivide(b *testing.B) {
	calc := New()
	for i := 0; i < b.N; i++ {
		_, _ = calc.Divide(12345.6789, 98765.4321)
	}
}
