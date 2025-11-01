package models

import "time"

// OTPRequest represents an OTP start request
type OTPRequest struct {
	Phone string `json:"phone" binding:"required"`
}

// OTPVerifyRequest represents an OTP verification request
type OTPVerifyRequest struct {
	Phone string `json:"phone" binding:"required"`
	Code  string `json:"code" binding:"required"`
}

// OTPResponse represents the response from OTP operations
type OTPResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message,omitempty"`
	UserID  string `json:"user_id,omitempty"`
}

// User represents a user in the system
type User struct {
	ID        string    `json:"id"`
	PhoneE164 string    `json:"phone_e164"`
	PhoneHash string    `json:"phone_hash"`
	CreatedAt time.Time `json:"created_at"`
}

// OTPData represents OTP data stored in Redis
type OTPData struct {
	Code      string    `json:"code"`
	Attempts  int       `json:"attempts"`
	ExpiresAt time.Time `json:"expires_at"`
	CreatedAt time.Time `json:"created_at"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
}
