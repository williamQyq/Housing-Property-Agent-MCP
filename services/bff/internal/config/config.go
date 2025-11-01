package config

import (
	"os"
	"strconv"
)

type Config struct {
	Port                  string
	IdentityServiceURL    string
	OrchestratorServiceURL string
	AgentServiceURL       string
	RedisURL              string
	JWTSecret             string
	Environment           string
}

func Load() *Config {
	return &Config{
		Port:                  getEnv("PORT", "8080"),
		IdentityServiceURL:    getEnv("IDENTITY_SERVICE_URL", "http://localhost:8081"),
		OrchestratorServiceURL: getEnv("ORCHESTRATOR_SERVICE_URL", "http://localhost:8082"),
		AgentServiceURL:       getEnv("AGENT_SERVICE_URL", "http://localhost:8083"),
		RedisURL:              getEnv("REDIS_URL", "redis://localhost:6379"),
		JWTSecret:             getEnv("JWT_SECRET", "your-secret-key"),
		Environment:           getEnv("ENVIRONMENT", "development"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}
