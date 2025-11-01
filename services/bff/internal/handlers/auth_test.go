package handlers

import (
	"bff/internal/models"
	"bff/internal/services"
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockIdentityService is a mock implementation of the IdentityService
type MockIdentityService struct {
	mock.Mock
}

func (m *MockIdentityService) StartOTP(req models.OTPRequest) (*models.OTPResponse, error) {
	args := m.Called(req)
	return args.Get(0).(*models.OTPResponse), args.Error(1)
}

func (m *MockIdentityService) VerifyOTP(req models.OTPVerifyRequest) (*models.OTPResponse, error) {
	args := m.Called(req)
	return args.Get(0).(*models.OTPResponse), args.Error(1)
}

func TestAuthHandler_StartOTP(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		requestBody    models.OTPRequest
		mockResponse   *models.OTPResponse
		mockError      error
		expectedStatus int
		expectedBody   map[string]interface{}
	}{
		{
			name: "successful OTP start",
			requestBody: models.OTPRequest{
				Phone: "+1234567890",
			},
			mockResponse: &models.OTPResponse{
				Success: true,
				Message: "OTP sent successfully",
			},
			mockError:      nil,
			expectedStatus: http.StatusOK,
			expectedBody: map[string]interface{}{
				"success": true,
				"message": "OTP sent successfully",
			},
		},
		{
			name: "invalid request body",
			requestBody: models.OTPRequest{
				Phone: "",
			},
			mockResponse:   nil,
			mockError:      nil,
			expectedStatus: http.StatusBadRequest,
			expectedBody: map[string]interface{}{
				"error": "invalid_request",
			},
		},
		{
			name: "service error",
			requestBody: models.OTPRequest{
				Phone: "+1234567890",
			},
			mockResponse:   nil,
			mockError:      assert.AnError,
			expectedStatus: http.StatusInternalServerError,
			expectedBody: map[string]interface{}{
				"error": "service_error",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock service
			mockService := new(MockIdentityService)
			if tt.mockResponse != nil {
				mockService.On("StartOTP", tt.requestBody).Return(tt.mockResponse, tt.mockError)
			}

			// Create handler
			handler := NewAuthHandler(mockService)

			// Create test router
			router := gin.New()
			router.POST("/otp/start", handler.StartOTP)

			// Create request
			jsonBody, _ := json.Marshal(tt.requestBody)
			req, _ := http.NewRequest("POST", "/otp/start", bytes.NewBuffer(jsonBody))
			req.Header.Set("Content-Type", "application/json")

			// Create response recorder
			w := httptest.NewRecorder()

			// Perform request
			router.ServeHTTP(w, req)

			// Assertions
			assert.Equal(t, tt.expectedStatus, w.Code)

			var response map[string]interface{}
			json.Unmarshal(w.Body.Bytes(), &response)

			for key, expectedValue := range tt.expectedBody {
				assert.Equal(t, expectedValue, response[key])
			}

			// Verify mock was called
			if tt.mockResponse != nil {
				mockService.AssertExpectations(t)
			}
		})
	}
}

func TestAuthHandler_VerifyOTP(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		requestBody    models.OTPVerifyRequest
		mockResponse   *models.OTPResponse
		mockError      error
		expectedStatus int
		expectedBody   map[string]interface{}
	}{
		{
			name: "successful OTP verification",
			requestBody: models.OTPVerifyRequest{
				Phone: "+1234567890",
				Code:  "123456",
			},
			mockResponse: &models.OTPResponse{
				Success: true,
				Message: "OTP verified successfully",
				UserID:  "user-123",
			},
			mockError:      nil,
			expectedStatus: http.StatusOK,
			expectedBody: map[string]interface{}{
				"success": true,
				"message": "OTP verified successfully",
				"user_id": "user-123",
			},
		},
		{
			name: "invalid OTP code",
			requestBody: models.OTPVerifyRequest{
				Phone: "+1234567890",
				Code:  "000000",
			},
			mockResponse: &models.OTPResponse{
				Success: false,
				Message: "Invalid OTP code",
			},
			mockError:      nil,
			expectedStatus: http.StatusUnauthorized,
			expectedBody: map[string]interface{}{
				"success": false,
				"message": "Invalid OTP code",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock service
			mockService := new(MockIdentityService)
			mockService.On("VerifyOTP", tt.requestBody).Return(tt.mockResponse, tt.mockError)

			// Create handler
			handler := NewAuthHandler(mockService)

			// Create test router
			router := gin.New()
			router.POST("/otp/verify", handler.VerifyOTP)

			// Create request
			jsonBody, _ := json.Marshal(tt.requestBody)
			req, _ := http.NewRequest("POST", "/otp/verify", bytes.NewBuffer(jsonBody))
			req.Header.Set("Content-Type", "application/json")

			// Create response recorder
			w := httptest.NewRecorder()

			// Perform request
			router.ServeHTTP(w, req)

			// Assertions
			assert.Equal(t, tt.expectedStatus, w.Code)

			var response map[string]interface{}
			json.Unmarshal(w.Body.Bytes(), &response)

			for key, expectedValue := range tt.expectedBody {
				assert.Equal(t, expectedValue, response[key])
			}

			// Verify mock was called
			mockService.AssertExpectations(t)
		})
	}
}
