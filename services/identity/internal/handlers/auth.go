package handlers

import (
	"identity/internal/models"
	"identity/internal/services"
	"identity/internal/utils"
	"net/http"

	"github.com/gin-gonic/gin"
)

type AuthHandler struct {
	otpService  *services.OTPService
	smsService  *services.SMSService
	userService *services.UserService
}

func NewAuthHandler(otpService *services.OTPService, smsService *services.SMSService, userService *services.UserService) *AuthHandler {
	return &AuthHandler{
		otpService:  otpService,
		smsService:  smsService,
		userService: userService,
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

	// Normalize phone number
	normalizedPhone, err := utils.NormalizePhone(req.Phone)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_phone",
			Message: "Invalid phone number format",
		})
		return
	}

	// Check rate limiting
	rateLimited, err := h.otpService.IsRateLimited(normalizedPhone)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "rate_limit_error",
			Message: "Failed to check rate limit",
		})
		return
	}

	if rateLimited {
		c.JSON(http.StatusTooManyRequests, models.ErrorResponse{
			Error:   "rate_limited",
			Message: "Too many OTP requests. Please try again later.",
		})
		return
	}

	// Generate and store OTP
	code, err := h.otpService.GenerateAndStoreOTP(normalizedPhone)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "otp_generation_error",
			Message: "Failed to generate OTP",
		})
		return
	}

	// Send SMS
	err = h.smsService.SendOTP(normalizedPhone, code)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "sms_error",
			Message: "Failed to send SMS",
		})
		return
	}

	// Increment rate limit counter
	h.otpService.IncrementRateLimit(normalizedPhone)

	// Return success response (don't reveal if phone exists)
	c.JSON(http.StatusOK, models.OTPResponse{
		Success: true,
		Message: "OTP sent successfully",
	})
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

	// Normalize phone number
	normalizedPhone, err := utils.NormalizePhone(req.Phone)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_phone",
			Message: "Invalid phone number format",
		})
		return
	}

	// Validate OTP format
	if !utils.ValidateOTP(req.Code) {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "invalid_otp",
			Message: "Invalid OTP format",
		})
		return
	}

	// Verify OTP
	valid, err := h.otpService.VerifyOTP(normalizedPhone, req.Code)
	if err != nil {
		c.JSON(http.StatusBadRequest, models.ErrorResponse{
			Error:   "otp_verification_error",
			Message: err.Error(),
		})
		return
	}

	if !valid {
		c.JSON(http.StatusUnauthorized, models.ErrorResponse{
			Error:   "invalid_otp",
			Message: "Invalid OTP code",
		})
		return
	}

	// Create or get user
	user, err := h.userService.CreateUser(normalizedPhone)
	if err != nil {
		c.JSON(http.StatusInternalServerError, models.ErrorResponse{
			Error:   "user_creation_error",
			Message: "Failed to create user",
		})
		return
	}

	// Return success response
	c.JSON(http.StatusOK, models.OTPResponse{
		Success: true,
		Message: "OTP verified successfully",
		UserID:  user.ID,
	})
}
