package services

import (
	"bff/internal/models"
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

type AgentService struct {
	baseURL string
	client  *http.Client
}

func NewAgentService(baseURL string) *AgentService {
	return &AgentService{
		baseURL: baseURL,
		client:  &http.Client{},
	}
}

func (s *AgentService) ExecuteTool(req models.ToolExecutionRequest) (*models.ToolExecutionResponse, error) {
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	resp, err := s.client.Post(s.baseURL+"/execute", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("failed to call agent service: %w", err)
	}
	defer resp.Body.Close()

	var toolResp models.ToolExecutionResponse
	if err := json.NewDecoder(resp.Body).Decode(&toolResp); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &toolResp, nil
}
