package services

import (
	"database/sql"
	"fmt"
	"time"

	"orchestrator/internal/models"

	"github.com/google/uuid"
)

type InviteService struct {
	db *sql.DB
}

func NewInviteService(db *sql.DB) *InviteService {
	return &InviteService{db: db}
}

func (s *InviteService) CreateInvite(req models.CreateInviteRequest) (*models.CreateInviteResponse, error) {
	// Check if user has permission to invite to this room
	// For now, we'll assume the inviter is a member of the room
	// In production, you'd want to verify this

	// Generate invite token
	token := uuid.New().String()
	inviteID := uuid.New().String()

	// Set expiry to 7 days from now
	expiresAt := time.Now().Add(7 * 24 * time.Hour)

	// Create invite
	query := `
		INSERT INTO invites (id, room_id, phone_e164, role, token, status, expires_at, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`

	_, err := s.db.Exec(query, inviteID, req.RoomID, req.Phone, req.Role, token, "PENDING", expiresAt, time.Now())
	if err != nil {
		return nil, fmt.Errorf("failed to create invite: %w", err)
	}

	return &models.CreateInviteResponse{
		InviteID: inviteID,
		Token:    token,
		Success:  true,
		Message:  "Invite created successfully",
	}, nil
}

func (s *InviteService) AcceptInvite(req models.AcceptInviteRequest) (*models.AcceptInviteResponse, error) {
	// Start transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Get invite details
	inviteQuery := `
		SELECT id, room_id, role, status, expires_at
		FROM invites
		WHERE token = $1
	`

	var invite models.Invite
	err = tx.QueryRow(inviteQuery, req.Token).Scan(
		&invite.ID,
		&invite.RoomID,
		&invite.Role,
		&invite.Status,
		&invite.ExpiresAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("invite not found")
		}
		return nil, fmt.Errorf("failed to get invite: %w", err)
	}

	// Check if invite is still valid
	if invite.Status != "PENDING" {
		return nil, fmt.Errorf("invite is no longer valid")
	}

	if time.Now().After(invite.ExpiresAt) {
		// Mark invite as expired
		tx.Exec("UPDATE invites SET status = 'EXPIRED' WHERE id = $1", invite.ID)
		return nil, fmt.Errorf("invite has expired")
	}

	// Check if user is already a member of the room
	membershipCheckQuery := `
		SELECT COUNT(*) FROM room_memberships
		WHERE room_id = $1 AND user_id = $2
	`

	var count int
	err = tx.QueryRow(membershipCheckQuery, invite.RoomID, req.UserID).Scan(&count)
	if err != nil {
		return nil, fmt.Errorf("failed to check membership: %w", err)
	}

	if count > 0 {
		// User is already a member, mark invite as accepted
		tx.Exec("UPDATE invites SET status = 'ACCEPTED' WHERE id = $1", invite.ID)
		return &models.AcceptInviteResponse{
			MembershipID: "existing",
			Success:      true,
			Message:      "User is already a member of this room",
		}, nil
	}

	// Create room membership
	membershipID := uuid.New().String()
	membershipQuery := `
		INSERT INTO room_memberships (id, room_id, user_id, role, created_at)
		VALUES ($1, $2, $3, $4, $5)
	`

	_, err = tx.Exec(membershipQuery, membershipID, invite.RoomID, req.UserID, invite.Role, time.Now())
	if err != nil {
		return nil, fmt.Errorf("failed to create membership: %w", err)
	}

	// Mark invite as accepted
	_, err = tx.Exec("UPDATE invites SET status = 'ACCEPTED' WHERE id = $1", invite.ID)
	if err != nil {
		return nil, fmt.Errorf("failed to update invite status: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return &models.AcceptInviteResponse{
		MembershipID: membershipID,
		Success:      true,
		Message:      "Successfully joined room",
	}, nil
}

func (s *InviteService) GetInviteByToken(token string) (*models.Invite, error) {
	query := `
		SELECT id, room_id, phone_e164, role, token, status, expires_at, created_at
		FROM invites
		WHERE token = $1
	`

	var invite models.Invite
	err := s.db.QueryRow(query, token).Scan(
		&invite.ID,
		&invite.RoomID,
		&invite.PhoneE164,
		&invite.Role,
		&invite.Token,
		&invite.Status,
		&invite.ExpiresAt,
		&invite.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("invite not found")
		}
		return nil, fmt.Errorf("failed to get invite: %w", err)
	}

	return &invite, nil
}
