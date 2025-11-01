package services

import (
	"bff/internal/models"
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

type OrchestratorService struct {
	baseURL string
	client  *http.Client
}

func NewOrchestratorService(baseURL string) *OrchestratorService {
	return &OrchestratorService{
		baseURL: baseURL,
		client:  &http.Client{},
	}
}

func (s *OrchestratorService) CreateRoom(userID string, req models.CreateRoomRequest) (*models.CreateRoomResponse, error) {
	// Add user ID to request
	roomReq := struct {
		Name          string `json:"name"`
		CreatorUserID string `json:"creator_user_id"`
		Role          string `json:"role"`
	}{
		Name:          req.Name,
		CreatorUserID: userID,
		Role:          req.Role,
	}

	jsonData, err := json.Marshal(roomReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := s.client.Post(s.baseURL+"/rooms", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call orchestrator service: %w", err)
	}
	defer resp.Body.Close()

	var roomResp models.CreateRoomResponse
	if err := json.NewDecoder(resp.Body).Decode(&roomResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &roomResp, nil
}

func (s *OrchestratorService) CreateInvite(userID, roomID string, req models.InviteRequest) (*models.InviteResponse, error) {
	// Add user ID and room ID to request
	inviteReq := struct {
		Phone         string `json:"phone"`
		Role          string `json:"role"`
		InviterUserID string `json:"inviter_user_id"`
		RoomID        string `json:"room_id"`
	}{
		Phone:         req.Phone,
		Role:          req.Role,
		InviterUserID: userID,
		RoomID:        roomID,
	}

	jsonData, err := json.Marshal(inviteReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := s.client.Post(s.baseURL+"/rooms/"+roomID+"/invites", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call orchestrator service: %w", err)
	}
	defer resp.Body.Close()

	var inviteResp models.InviteResponse
	if err := json.NewDecoder(resp.Body).Decode(&inviteResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &inviteResp, nil
}

func (s *OrchestratorService) AcceptInvite(userID string, req models.AcceptInviteRequest) (*models.AcceptInviteResponse, error) {
	// Add user ID to request
	acceptReq := struct {
		Token  string `json:"token"`
		UserID string `json:"user_id"`
	}{
		Token:  req.Token,
		UserID: userID,
	}

	jsonData, err := json.Marshal(acceptReq)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := s.client.Post(s.baseURL+"/invites/"+req.Token+"/accept", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call orchestrator service: %w", err)
	}
	defer resp.Body.Close()

	var acceptResp models.AcceptInviteResponse
	if err := json.NewDecoder(resp.Body).Decode(&acceptResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &acceptResp, nil
}
