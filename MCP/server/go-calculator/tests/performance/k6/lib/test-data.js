/**
 * Test data generators for k6 performance tests
 * Provides random test data for calculator operations
 */

/**
 * Generate a random integer between min and max (inclusive)
 */
export function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Generate a random float between min and max
 */
export function randomFloat(min, max, decimals = 2) {
  const value = Math.random() * (max - min) + min;
  return parseFloat(value.toFixed(decimals));
}

/**
 * Generate random number pairs for testing
 */
export function generateNumberPair(type = 'mixed') {
  switch (type) {
    case 'small':
      // Small integers (1-100)
      return {
        a: randomInt(1, 100),
        b: randomInt(1, 100),
      };

    case 'large':
      // Large integers (1000-100000)
      return {
        a: randomInt(1000, 100000),
        b: randomInt(1000, 100000),
      };

    case 'decimal':
      // Decimal numbers (0.01-1000.99)
      return {
        a: randomFloat(0.01, 1000, 4),
        b: randomFloat(0.01, 1000, 4),
      };

    case 'negative':
      // Negative numbers (-1000 to -1)
      return {
        a: randomInt(-1000, -1),
        b: randomInt(-1000, -1),
      };

    case 'mixed':
    default:
      // Mixed: positive, negative, decimals
      const types = ['small', 'large', 'decimal', 'negative'];
      const randomType = types[randomInt(0, types.length - 1)];
      return generateNumberPair(randomType);
  }
}

/**
 * Generate test data for specific operations
 */
export function generateOperationData(operation) {
  switch (operation) {
    case 'add':
    case 'subtract':
    case 'multiply':
      return generateNumberPair('mixed');

    case 'divide':
      // For division, ensure b is not zero and not too small
      const pair = generateNumberPair('mixed');
      // Avoid division by zero and very small divisors
      while (Math.abs(pair.b) < 0.001) {
        pair.b = randomFloat(1, 100, 2);
      }
      return pair;

    default:
      return generateNumberPair('mixed');
  }
}

/**
 * Select a random calculator operation
 */
export function selectRandomOperation(distribution = null) {
  // Default distribution: 40% add, 30% subtract, 20% multiply, 10% divide
  const defaultDistribution = {
    add: 40,
    subtract: 30,
    multiply: 20,
    divide: 10,
  };

  const dist = distribution || defaultDistribution;
  const operations = [];

  // Build weighted array
  for (const [op, weight] of Object.entries(dist)) {
    for (let i = 0; i < weight; i++) {
      operations.push(op);
    }
  }

  // Select random operation from weighted array
  const randomIndex = randomInt(0, operations.length - 1);
  return operations[randomIndex];
}

/**
 * Generate a batch of test cases
 */
export function generateTestBatch(count = 100, operation = null) {
  const batch = [];

  for (let i = 0; i < count; i++) {
    const op = operation || selectRandomOperation();
    const data = generateOperationData(op);

    batch.push({
      operation: op,
      a: data.a,
      b: data.b,
    });
  }

  return batch;
}

/**
 * Get expected result for an operation (for validation)
 */
export function getExpectedResult(operation, a, b) {
  switch (operation) {
    case 'add':
      return a + b;
    case 'subtract':
      return a - b;
    case 'multiply':
      return a * b;
    case 'divide':
      if (b === 0) {
        return null; // Division by zero
      }
      return a / b;
    default:
      return null;
  }
}

/**
 * Validate calculator result within epsilon tolerance
 */
export function validateResult(actual, expected, epsilon = 0.0001) {
  if (expected === null) {
    return actual === null;
  }

  const actualNum = parseFloat(actual);
  const expectedNum = parseFloat(expected);

  if (isNaN(actualNum) || isNaN(expectedNum)) {
    return false;
  }

  return Math.abs(actualNum - expectedNum) < epsilon;
}

/**
 * Generate edge case test data
 */
export function generateEdgeCases() {
  return [
    // Zero operations
    { operation: 'add', a: 0, b: 0, description: 'zero + zero' },
    { operation: 'add', a: 5, b: 0, description: 'number + zero' },
    { operation: 'subtract', a: 0, b: 5, description: 'zero - number' },
    { operation: 'multiply', a: 0, b: 100, description: 'zero * number' },
    { operation: 'divide', a: 0, b: 5, description: 'zero / number' },

    // Large numbers
    { operation: 'add', a: 999999, b: 999999, description: 'large + large' },
    { operation: 'multiply', a: 99999, b: 99999, description: 'large * large' },

    // Small decimals
    { operation: 'add', a: 0.0001, b: 0.0001, description: 'small decimal + small decimal' },
    { operation: 'divide', a: 1, b: 3, description: '1 / 3 (repeating decimal)' },

    // Negative numbers
    { operation: 'add', a: -5, b: -3, description: 'negative + negative' },
    { operation: 'subtract', a: -5, b: 3, description: 'negative - positive' },
    { operation: 'multiply', a: -5, b: -3, description: 'negative * negative' },
    { operation: 'divide', a: -10, b: 2, description: 'negative / positive' },

    // Mixed signs
    { operation: 'add', a: 5, b: -3, description: 'positive + negative' },
    { operation: 'multiply', a: 5, b: -3, description: 'positive * negative' },
  ];
}

/**
 * Distribution presets for different test scenarios
 */
export const OperationDistributions = {
  balanced: {
    add: 25,
    subtract: 25,
    multiply: 25,
    divide: 25,
  },
  realistic: {
    add: 40,
    subtract: 30,
    multiply: 20,
    divide: 10,
  },
  addHeavy: {
    add: 70,
    subtract: 15,
    multiply: 10,
    divide: 5,
  },
  divideHeavy: {
    add: 20,
    subtract: 20,
    multiply: 20,
    divide: 40,
  },
};
