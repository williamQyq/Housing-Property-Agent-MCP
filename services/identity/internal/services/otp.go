package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"identity/internal/models"
	"identity/internal/utils"

	"github.com/redis/go-redis/v9"
)

type OTPService struct {
	rdb       *redis.Client
	secret    string
	expiry    time.Duration
	maxAttempts int
}

func NewOTPService(rdb *redis.Client, secret string) *OTPService {
	return &OTPService{
		rdb:       rdb,
		secret:    secret,
		expiry:    5 * time.Minute, // 5 minutes
		maxAttempts: 5,
	}
}

func (s *OTPService) GenerateAndStoreOTP(phone string) (string, error) {
	// Generate OTP
	code, err := utils.GenerateOTP()
	if err != nil {
		return "", fmt.Errorf("failed to generate OTP: %w", err)
	}

	// Create OTP data
	otpData := models.OTPData{
		Code:      code,
		Attempts:  0,
		ExpiresAt: time.Now().Add(s.expiry),
		CreatedAt: time.Now(),
	}

	// Serialize OTP data
	jsonData, err := json.Marshal(otpData)
	if err != nil {
		return "", fmt.Errorf("failed to marshal OTP data: %w", err)
	}

	// Store in Redis with expiry
	key := fmt.Sprintf("otp:%s", phone)
	err = s.rdb.Set(context.Background(), key, jsonData, s.expiry).Err()
	if err != nil {
		return "", fmt.Errorf("failed to store OTP: %w", err)
	}

	return code, nil
}

func (s *OTPService) VerifyOTP(phone, code string) (bool, error) {
	key := fmt.Sprintf("otp:%s", phone)
	
	// Get OTP data from Redis
	jsonData, err := s.rdb.Get(context.Background(), key).Result()
	if err != nil {
		if err == redis.Nil {
			return false, fmt.Errorf("OTP not found or expired")
		}
		return false, fmt.Errorf("failed to get OTP: %w", err)
	}

	// Deserialize OTP data
	var otpData models.OTPData
	err = json.Unmarshal([]byte(jsonData), &otpData)
	if err != nil {
		return false, fmt.Errorf("failed to unmarshal OTP data: %w", err)
	}

	// Check if OTP has expired
	if time.Now().After(otpData.ExpiresAt) {
		// Clean up expired OTP
		s.rdb.Del(context.Background(), key)
		return false, fmt.Errorf("OTP expired")
	}

	// Check if max attempts exceeded
	if otpData.Attempts >= s.maxAttempts {
		// Clean up after max attempts
		s.rdb.Del(context.Background(), key)
		return false, fmt.Errorf("max OTP attempts exceeded")
	}

	// Increment attempts
	otpData.Attempts++

	// Check if code matches
	if otpData.Code == code {
		// OTP is correct, clean up
		s.rdb.Del(context.Background(), key)
		return true, nil
	}

	// Code doesn't match, update attempts
	updatedData, _ := json.Marshal(otpData)
	s.rdb.Set(context.Background(), key, updatedData, s.expiry)
	
	return false, fmt.Errorf("invalid OTP code")
}

func (s *OTPService) IsRateLimited(phone string) (bool, error) {
	key := fmt.Sprintf("rate_limit:%s", phone)
	
	// Check current count
	count, err := s.rdb.Get(context.Background(), key).Int()
	if err != nil && err != redis.Nil {
		return false, fmt.Errorf("failed to check rate limit: %w", err)
	}

	// If count is 0 or key doesn't exist, not rate limited
	if count == 0 {
		return false, nil
	}

	// Check if count exceeds limit
	return count >= 10, nil // 10 requests per window
}

func (s *OTPService) IncrementRateLimit(phone string) error {
	key := fmt.Sprintf("rate_limit:%s", phone)
	
	// Increment counter with expiry
	pipe := s.rdb.Pipeline()
	pipe.Incr(context.Background(), key)
	pipe.Expire(context.Background(), key, time.Minute) // 1 minute window
	_, err := pipe.Exec(context.Background())
	
	return err
}
