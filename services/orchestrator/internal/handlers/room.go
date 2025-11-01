package handlers

import (
	"orchestrator/internal/models"
	"orchestrator/internal/services"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

type RoomHandler struct {
	roomService *services.RoomService
}

func NewRoomHandler(roomService *services.RoomService) *RoomHandler {
	return &RoomHandler{
		roomService: roomService,
	}
}

func (h *RoomHandler) CreateRoom(c *gin.Context) {
	var req models.CreateRoomRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	// Get user ID from query parameter (in production, this would come from JWT)
	userID := c.Query("user_id")
	if userID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_user_id",
			Message: "user_id is required",
		})
		return
	}

	req.CreatorUserID = userID

	// Create room
	resp, err := h.roomService.CreateRoom(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "room_creation_error",
			Message: "Failed to create room",
		})
		return
	}

	c.JSON(http.StatusCreated, resp)
}

func (h *RoomHandler) ListRooms(c *gin.Context) {
	// Get user ID from query parameter
	userID := c.Query("user_id")
	if userID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_user_id",
			Message: "user_id is required",
		})
		return
	}

	// Get rooms for user
	rooms, err := h.roomService.ListRooms(userID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "room_list_error",
			Message: "Failed to list rooms",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"rooms": rooms,
	})
}

func (h *RoomHandler) GetRoom(c *gin.Context) {
	roomID := c.Param("id")
	if roomID == "" {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "missing_room_id",
			Message: "room_id is required",
		})
		return
	}

	// Get room
	room, err := h.roomService.GetRoom(roomID)
	if err != nil {
		c.JSON(http.StatusNotFound, models.ErrorResponse{
			Error:   "room_not_found",
			Message: "Room not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"room": room,
	})
}
