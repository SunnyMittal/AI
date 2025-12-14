package config

import (
	"os"
	"testing"
	"time"
)

func TestLoad(t *testing.T) {
	// Set test environment variables
	os.Setenv("SERVER_PORT", "9090")
	os.Setenv("LOG_LEVEL", "debug")
	defer func() {
		os.Unsetenv("SERVER_PORT")
		os.Unsetenv("LOG_LEVEL")
	}()

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() failed: %v", err)
	}

	if cfg.Server.Port != "9090" {
		t.Errorf("Expected port 9090, got %s", cfg.Server.Port)
	}

	if cfg.Log.Level != "debug" {
		t.Errorf("Expected log level debug, got %s", cfg.Log.Level)
	}
}

func TestLoadDefaults(t *testing.T) {
	// Clear all environment variables
	vars := []string{"SERVER_PORT", "SERVER_HOST", "LOG_LEVEL", "LOG_ENCODING", "API_VERSION"}
	for _, v := range vars {
		os.Unsetenv(v)
	}

	cfg, err := Load()
	if err != nil {
		t.Fatalf("Load() failed: %v", err)
	}

	if cfg.Server.Port != "8080" {
		t.Errorf("Expected default port 8080, got %s", cfg.Server.Port)
	}

	if cfg.Log.Level != "info" {
		t.Errorf("Expected default log level info, got %s", cfg.Log.Level)
	}

	if cfg.Log.Encoding != "json" {
		t.Errorf("Expected default encoding json, got %s", cfg.Log.Encoding)
	}
}

func TestValidate_InvalidLogLevel(t *testing.T) {
	cfg := &Config{
		Server: ServerConfig{Port: "8080"},
		Log:    LogConfig{Level: "invalid", Encoding: "json"},
	}

	err := cfg.Validate()
	if err == nil {
		t.Error("Expected validation error for invalid log level")
	}
}

func TestValidate_InvalidEncoding(t *testing.T) {
	cfg := &Config{
		Server: ServerConfig{Port: "8080"},
		Log:    LogConfig{Level: "info", Encoding: "invalid"},
	}

	err := cfg.Validate()
	if err == nil {
		t.Error("Expected validation error for invalid encoding")
	}
}

func TestValidate_EmptyPort(t *testing.T) {
	cfg := &Config{
		Server: ServerConfig{Port: ""},
		Log:    LogConfig{Level: "info", Encoding: "json"},
	}

	err := cfg.Validate()
	if err == nil {
		t.Error("Expected validation error for empty port")
	}
}

func TestAddress(t *testing.T) {
	cfg := &Config{
		Server: ServerConfig{
			Host: "example.com",
			Port: "8080",
		},
	}

	expected := "example.com:8080"
	if cfg.Address() != expected {
		t.Errorf("Expected address %s, got %s", expected, cfg.Address())
	}
}

func TestParseDurationOrDefault(t *testing.T) {
	tests := []struct {
		name         string
		envValue     string
		defaultValue time.Duration
		expected     time.Duration
	}{
		{"valid duration", "30s", 15 * time.Second, 30 * time.Second},
		{"invalid duration", "invalid", 15 * time.Second, 15 * time.Second},
		{"empty value", "", 15 * time.Second, 15 * time.Second},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envValue != "" {
				os.Setenv("TEST_DURATION", tt.envValue)
				defer os.Unsetenv("TEST_DURATION")
			} else {
				os.Unsetenv("TEST_DURATION")
			}

			result := parseDurationOrDefault("TEST_DURATION", tt.defaultValue)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

func TestGetEnvOrDefault(t *testing.T) {
	tests := []struct {
		name         string
		key          string
		envValue     string
		defaultValue string
		expected     string
	}{
		{"env set", "TEST_KEY", "test_value", "default", "test_value"},
		{"env empty", "TEST_KEY", "", "default", "default"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.envValue != "" {
				os.Setenv(tt.key, tt.envValue)
				defer os.Unsetenv(tt.key)
			} else {
				os.Unsetenv(tt.key)
			}

			result := getEnvOrDefault(tt.key, tt.defaultValue)
			if result != tt.expected {
				t.Errorf("Expected %s, got %s", tt.expected, result)
			}
		})
	}
}
