package handlers

import (
	"bff/internal/models"
	"bff/internal/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

type AgentHandler struct {
	agentService *services.AgentService
}

func NewAgentHandler(agentService *services.AgentService) *AgentHandler {
	return &AgentHandler{
		agentService: agentService,
	}
}

func (h *AgentHandler) ExecuteTool(c *gin.Context) {
	// Get user ID from context (set by auth middleware)
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "unauthorized",
			Message: "User ID not found in context",
		})
		return
	}

	var req models.ToolExecutionRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	// Add user context to tool input
	if req.Input == nil {
		req.Input = make(map[string]interface{})
	}
	req.Input["user_id"] = userID

	// Call agent service
	resp, err := h.agentService.ExecuteTool(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "service_error",
			Message: "Failed to execute tool",
		})
		return
	}

	c.JSON(http.StatusOK, resp)
}
