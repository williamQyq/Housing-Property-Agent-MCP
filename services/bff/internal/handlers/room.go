package handlers

import (
	"bff/internal/models"
	"bff/internal/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

type RoomHandler struct {
	orchestratorService *services.OrchestratorService
}

func NewRoomHandler(orchestratorService *services.OrchestratorService) *RoomHandler {
	return &RoomHandler{
		orchestratorService: orchestratorService,
	}
}

func (h *RoomHandler) CreateRoom(c *gin.Context) {
	// Get user ID from context (set by auth middleware)
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "unauthorized",
			Message: "User ID not found in context",
		})
		return
	}

	var req models.CreateRoomRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	// Call orchestrator service
	resp, err := h.orchestratorService.CreateRoom(userID.(string), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "service_error",
			Message: "Failed to create room",
		})
		return
	}

	c.JSON(http.StatusCreated, resp)
}

func (h *RoomHandler) ListRooms(c *gin.Context) {
	// Get user ID from context
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "unauthorized",
			Message: "User ID not found in context",
		})
		return
	}

	// For now, return empty list - would call orchestrator service
	c.JSON(http.StatusOK, gin.H{
		"rooms": []models.Room{},
		"user_id": userID,
	})
}

func (h *RoomHandler) GetRoom(c *gin.Context) {
	roomID := c.Param("id")
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "unauthorized",
			Message: "User ID not found in context",
		})
		return
	}

	// For now, return placeholder - would call orchestrator service
	c.JSON(http.StatusOK, gin.H{
		"room": gin.H{
			"id": roomID,
			"user_id": userID,
		},
	})
}

func (h *RoomHandler) CreateInvite(c *gin.Context) {
	roomID := c.Param("id")
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "unauthorized",
			Message: "User ID not found in context",
		})
		return
	}

	var req models.InviteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	// Call orchestrator service
	resp, err := h.orchestratorService.CreateInvite(userID.(string), roomID, req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "service_error",
			Message: "Failed to create invite",
		})
		return
	}

	c.JSON(http.StatusCreated, resp)
}

func (h *RoomHandler) AcceptInvite(c *gin.Context) {
	token := c.Param("token")
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "unauthorized",
			Message: "User ID not found in context",
		})
		return
	}

	req := models.AcceptInviteRequest{
		Token: token,
	}

	// Call orchestrator service
	resp, err := h.orchestratorService.AcceptInvite(userID.(string), req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "service_error",
			Message: "Failed to accept invite",
		})
		return
	}

	c.JSON(http.StatusOK, resp)
}
