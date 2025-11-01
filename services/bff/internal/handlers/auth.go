package handlers

import (
	"bff/internal/models"
	"bff/internal/services"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

type AuthHandler struct {
	identityService *services.IdentityService
}

func NewAuthHandler(identityService *services.IdentityService) *AuthHandler {
	return &AuthHandler{
		identityService: identityService,
	}
}

func (h *AuthHandler) StartOTP(c *gin.Context) {
	var req models.OTPRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	// Call identity service
	resp, err := h.identityService.StartOTP(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "service_error",
			Message: "Failed to start OTP process",
		})
		return
	}

	c.JSON(http.StatusOK, resp)
}

func (h *AuthHandler) VerifyOTP(c *gin.Context) {
	var req models.OTPVerifyRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_request",
			Message: err.Error(),
		})
		return
	}

	// Call identity service
	resp, err := h.identityService.VerifyOTP(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "service_error",
			Message: "Failed to verify OTP",
		})
		return
	}

	if !resp.Success {
		c.JSON(http.StatusUnauthorized, resp)
		return
	}

	// Generate JWT token
	token, err := h.generateJWT(resp.UserID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "token_error",
			Message: "Failed to generate token",
		})
		return
	}

	resp.Token = token
	c.JSON(http.StatusOK, resp)
}

func (h *AuthHandler) RefreshToken(c *gin.Context) {
	// Extract user ID from context (set by auth middleware)
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "unauthorized",
			Message: "User ID not found in context",
		})
		return
	}

	// Generate new JWT token
	token, err := h.generateJWT(userID.(string))
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "token_error",
			Message: "Failed to generate token",
		})
		return
	}

	c.JSON(http.StatusOK, models.OTPResponse{
		Success: true,
		Token:   token,
	})
}

func (h *AuthHandler) generateJWT(userID string) (string, error) {
	// Create JWT claims
	claims := jwt.MapClaims{
		"user_id": userID,
		"jti":     uuid.New().String(), // JWT ID for uniqueness
	}

	// Create token
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)

	// Sign token with secret key
	tokenString, err := token.SignedString([]byte("your-secret-key"))
	if err != nil {
		return "", err
	}

	return tokenString, nil
}
