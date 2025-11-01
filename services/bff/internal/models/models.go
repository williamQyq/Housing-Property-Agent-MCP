package models

import "time"

// User represents a user in the system
type User struct {
	ID        string    `json:"id"`
	PhoneE164 string    `json:"phone_e164"`
	CreatedAt time.Time `json:"created_at"`
}

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
	Token   string `json:"token,omitempty"`
}

// Room represents a room/group in the system
type Room struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	OwnerUserID string    `json:"owner_user_id"`
	CreatedAt   time.Time `json:"created_at"`
}

// CreateRoomRequest represents a room creation request
type CreateRoomRequest struct {
	Name string `json:"name" binding:"required"`
	Role string `json:"role" binding:"required,oneof=LANDLORD TENANT"`
}

// CreateRoomResponse represents the response from room creation
type CreateRoomResponse struct {
	RoomID string `json:"room_id"`
	Success bool   `json:"success"`
	Message string `json:"message,omitempty"`
}

// InviteRequest represents an invite creation request
type InviteRequest struct {
	Phone string `json:"phone" binding:"required"`
	Role  string `json:"role" binding:"required,oneof=LANDLORD TENANT"`
}

// InviteResponse represents the response from invite operations
type InviteResponse struct {
	InviteID string `json:"invite_id"`
	Token    string `json:"token"`
	Success  bool   `json:"success"`
	Message  string `json:"message,omitempty"`
}

// AcceptInviteRequest represents an invite acceptance request
type AcceptInviteRequest struct {
	Token string `json:"token" binding:"required"`
}

// AcceptInviteResponse represents the response from invite acceptance
type AcceptInviteResponse struct {
	MembershipID string `json:"membership_id"`
	Success      bool   `json:"success"`
	Message      string `json:"message,omitempty"`
}

// ToolExecutionRequest represents a tool execution request
type ToolExecutionRequest struct {
	ToolName string                 `json:"tool_name" binding:"required"`
	Input    map[string]interface{} `json:"input" binding:"required"`
}

// ToolExecutionResponse represents the response from tool execution
type ToolExecutionResponse struct {
	Result  interface{} `json:"result"`
	Success bool        `json:"success"`
	Error   string      `json:"error,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
}
