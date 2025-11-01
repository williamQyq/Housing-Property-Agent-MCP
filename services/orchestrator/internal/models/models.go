package models

import (
	"time"
)

// Role represents user roles in rooms
type Role string

const (
	RoleLandlord Role = "LANDLORD"
	RoleTenant   Role = "TENANT"
)

// Room represents a room/group in the system
type Room struct {
	ID          string    `json:"id" db:"id"`
	Name        string    `json:"name" db:"name"`
	OwnerUserID string    `json:"owner_user_id" db:"owner_user_id"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
}

// RoomMembership represents a user's membership in a room
type RoomMembership struct {
	ID        string    `json:"id" db:"id"`
	RoomID    string    `json:"room_id" db:"room_id"`
	UserID    string    `json:"user_id" db:"user_id"`
	Role      Role      `json:"role" db:"role"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// Invite represents an invitation to join a room
type Invite struct {
	ID        string    `json:"id" db:"id"`
	RoomID    string    `json:"room_id" db:"room_id"`
	PhoneE164 string    `json:"phone_e164" db:"phone_e164"`
	Role      Role      `json:"role" db:"role"`
	Token     string    `json:"token" db:"token"`
	Status    string    `json:"status" db:"status"`
	ExpiresAt time.Time `json:"expires_at" db:"expires_at"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// CreateRoomRequest represents a room creation request
type CreateRoomRequest struct {
	Name          string `json:"name" binding:"required"`
	CreatorUserID string `json:"creator_user_id" binding:"required"`
	Role          string `json:"role" binding:"required,oneof=LANDLORD TENANT"`
}

// CreateRoomResponse represents the response from room creation
type CreateRoomResponse struct {
	RoomID  string `json:"room_id"`
	Success bool   `json:"success"`
	Message string `json:"message,omitempty"`
}

// CreateInviteRequest represents an invite creation request
type CreateInviteRequest struct {
	Phone         string `json:"phone" binding:"required"`
	Role          string `json:"role" binding:"required,oneof=LANDLORD TENANT"`
	InviterUserID string `json:"inviter_user_id" binding:"required"`
	RoomID        string `json:"room_id" binding:"required"`
}

// CreateInviteResponse represents the response from invite creation
type CreateInviteResponse struct {
	InviteID string `json:"invite_id"`
	Token    string `json:"token"`
	Success  bool   `json:"success"`
	Message  string `json:"message,omitempty"`
}

// AcceptInviteRequest represents an invite acceptance request
type AcceptInviteRequest struct {
	Token  string `json:"token" binding:"required"`
	UserID string `json:"user_id" binding:"required"`
}

// AcceptInviteResponse represents the response from invite acceptance
type AcceptInviteResponse struct {
	MembershipID string `json:"membership_id"`
	Success      bool   `json:"success"`
	Message      string `json:"message,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message,omitempty"`
}
