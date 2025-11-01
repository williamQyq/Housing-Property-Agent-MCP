package services

import (
	"bff/internal/models"
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

type IdentityService struct {
	baseURL string
	client  *http.Client
}

func NewIdentityService(baseURL string) *IdentityService {
	return &IdentityService{
		baseURL: baseURL,
		client:  &http.Client{},
	}
}

func (s *IdentityService) StartOTP(req models.OTPRequest) (*models.OTPResponse, error) {
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := s.client.Post(s.baseURL+"/otp/start", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call identity service: %w", err)
	}
	defer resp.Body.Close()

	var otpResp models.OTPResponse
	if err := json.NewDecoder(resp.Body).Decode(&otpResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &otpResp, nil
}

func (s *IdentityService) VerifyOTP(req models.OTPVerifyRequest) (*models.OTPResponse, error) {
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := s.client.Post(s.baseURL+"/otp/verify", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call identity service: %w", err)
	}
	defer resp.Body.Close()

	var otpResp models.OTPResponse
	if err := json.NewDecoder(resp.Body).Decode(&otpResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &otpResp, nil
}
