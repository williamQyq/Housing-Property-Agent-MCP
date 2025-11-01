package services

import (
	"database/sql"
	"fmt"
	"time"

	"orchestrator/internal/models"

	"github.com/google/uuid"
)

type RoomService struct {
	db *sql.DB
}

func NewRoomService(db *sql.DB) *RoomService {
	return &RoomService{db: db}
}

func (s *RoomService) CreateRoom(req models.CreateRoomRequest) (*models.CreateRoomResponse, error) {
	// Start transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Create room
	roomID := uuid.New().String()
	roomQuery := `
		INSERT INTO rooms (id, name, owner_user_id, created_at)
		VALUES ($1, $2, $3, $4)
	`
	_, err = tx.Exec(roomQuery, roomID, req.Name, req.CreatorUserID, time.Now())
	if err != nil {
		return nil, fmt.Errorf("failed to create room: %w", err)
	}

	// Create membership for creator
	membershipID := uuid.New().String()
	membershipQuery := `
		INSERT INTO room_memberships (id, room_id, user_id, role, created_at)
		VALUES ($1, $2, $3, $4, $5)
	`
	_, err = tx.Exec(membershipQuery, membershipID, roomID, req.CreatorUserID, req.Role, time.Now())
	if err != nil {
		return nil, fmt.Errorf("failed to create membership: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return nil, fmt.Errorf("failed to commit transaction: %w", err)
	}

	return &models.CreateRoomResponse{
		RoomID:  roomID,
		Success: true,
		Message: "Room created successfully",
	}, nil
}

func (s *RoomService) GetRoom(roomID string) (*models.Room, error) {
	query := `
		SELECT id, name, owner_user_id, created_at
		FROM rooms
		WHERE id = $1
	`

	var room models.Room
	err := s.db.QueryRow(query, roomID).Scan(
		&room.ID,
		&room.Name,
		&room.OwnerUserID,
		&room.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("room not found")
		}
		return nil, fmt.Errorf("failed to get room: %w", err)
	}

	return &room, nil
}

func (s *RoomService) ListRooms(userID string) ([]models.Room, error) {
	query := `
		SELECT r.id, r.name, r.owner_user_id, r.created_at
		FROM rooms r
		INNER JOIN room_memberships rm ON r.id = rm.room_id
		WHERE rm.user_id = $1
		ORDER BY r.created_at DESC
	`

	rows, err := s.db.Query(query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to query rooms: %w", err)
	}
	defer rows.Close()

	var rooms []models.Room
	for rows.Next() {
		var room models.Room
		err := rows.Scan(
			&room.ID,
			&room.Name,
			&room.OwnerUserID,
			&room.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan room: %w", err)
		}
		rooms = append(rooms, room)
	}

	return rooms, nil
}

func (s *RoomService) GetUserRoleInRoom(userID, roomID string) (models.Role, error) {
	query := `
		SELECT role
		FROM room_memberships
		WHERE room_id = $1 AND user_id = $2
	`

	var role models.Role
	err := s.db.QueryRow(query, roomID, userID).Scan(&role)
	if err != nil {
		if err == sql.ErrNoRows {
			return "", fmt.Errorf("user not found in room")
		}
		return "", fmt.Errorf("failed to get user role: %w", err)
	}

	return role, nil
}
