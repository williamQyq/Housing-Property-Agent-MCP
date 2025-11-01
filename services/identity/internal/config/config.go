package config

import (
	"os"
	"strconv"
)

type Config struct {
	Port                string
	RedisURL            string
	OTPSecret           string
	TwilioAccountSID    string
	TwilioAuthToken     string
	TwilioPhoneNumber   string
	Environment         string
	OTPExpiryMinutes    int
	MaxOTPAttempts      int
	RateLimitWindow     int
	RateLimitMaxRequests int
}

func Load() *Config {
	return &Config{
		Port:                getEnv("PORT", "8081"),
		RedisURL:            getEnv("REDIS_URL", "localhost:6379"),
		OTPSecret:           getEnv("OTP_SECRET", "your-otp-secret-key"),
		TwilioAccountSID:    getEnv("TWILIO_ACCOUNT_SID", ""),
		TwilioAuthToken:     getEnv("TWILIO_AUTH_TOKEN", ""),
		TwilioPhoneNumber:   getEnv("TWILIO_PHONE_NUMBER", ""),
		Environment:         getEnv("ENVIRONMENT", "development"),
		OTPExpiryMinutes:    getEnvAsInt("OTP_EXPIRY_MINUTES", 5),
		MaxOTPAttempts:      getEnvAsInt("MAX_OTP_ATTEMPTS", 5),
		RateLimitWindow:     getEnvAsInt("RATE_LIMIT_WINDOW", 60),
		RateLimitMaxRequests: getEnvAsInt("RATE_LIMIT_MAX_REQUESTS", 10),
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
