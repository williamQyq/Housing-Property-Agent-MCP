package handlers

import (
	"orchestrator/internal/models"
	"orchestrator/internal/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

type InviteHandler struct {
	inviteService *services.InviteService
}

func NewInviteHandler(inviteService *services.InviteService) *InviteHandler {
	return &InviteHandler{
		inviteService: inviteService,
	}
}

func (h *InviteHandler) CreateInvite(c *gin.Context) {
	roomID := c.Param("id")
	if roomID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_room_id",
			Message: "room_id is required",
		})
		return
	}

	var req models.CreateInviteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	// Get user ID from query parameter
	userID := c.Query("user_id")
	if userID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_user_id",
			Message: "user_id is required",
		})
		return
	}

	req.RoomID = roomID
	req.InviterUserID = userID

	// Create invite
	resp, err := h.inviteService.CreateInvite(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "invite_creation_error",
			Message: "Failed to create invite",
		})
		return
	}

	c.JSON(http.StatusCreated, resp)
}

func (h *InviteHandler) AcceptInvite(c *gin.Context) {
	token := c.Param("token")
	if token == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_token",
			Message: "token is required",
		})
		return
	}

	var req models.AcceptInviteRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	req.Token = token

	// Accept invite
	resp, err := h.inviteService.AcceptInvite(req)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invite_acceptance_error",
			Message: err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, resp)
}
