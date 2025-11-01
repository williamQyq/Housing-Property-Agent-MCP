package handlers

import (
	"identity/internal/models"
	"identity/internal/services"
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// MockOTPService is a mock implementation of the OTPService
type MockOTPService struct {
	mock.Mock
}

func (m *MockOTPService) GenerateAndStoreOTP(phone string) (string, error) {
	args := m.Called(phone)
	return args.String(0), args.Error(1)
}

func (m *MockOTPService) VerifyOTP(phone, code string) (bool, error) {
	args := m.Called(phone, code)
	return args.Bool(0), args.Error(1)
}

func (m *MockOTPService) IsRateLimited(phone string) (bool, error) {
	args := m.Called(phone)
	return args.Bool(0), args.Error(1)
}

func (m *MockOTPService) IncrementRateLimit(phone string) error {
	args := m.Called(phone)
	return args.Error(0)
}

// MockSMSService is a mock implementation of the SMSService
type MockSMSService struct {
	mock.Mock
}

func (m *MockSMSService) SendOTP(phone, code string) error {
	args := m.Called(phone, code)
	return args.Error(0)
}

func (m *MockSMSService) SendInvite(phone, inviteLink string) error {
	args := m.Called(phone, inviteLink)
	return args.Error(0)
}

// MockUserService is a mock implementation of the UserService
type MockUserService struct {
	mock.Mock
}

func (m *MockUserService) CreateUser(phone string) (*models.User, error) {
	args := m.Called(phone)
	return args.Get(0).(*models.User), args.Error(1)
}

func (m *MockUserService) GetUserByID(userID string) (*models.User, error) {
	args := m.Called(userID)
	return args.Get(0).(*models.User), args.Error(1)
}

func (m *MockUserService) GetUserByPhoneHash(phoneHash string) (*models.User, error) {
	args := m.Called(phoneHash)
	return args.Get(0).(*models.User), args.Error(1)
}

func (m *MockUserService) GetUserByPhone(phone string) (*models.User, error) {
	args := m.Called(phone)
	return args.Get(0).(*models.User), args.Error(1)
}

func TestAuthHandler_StartOTP(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		requestBody    models.OTPRequest
		mockSetup      func(*MockOTPService, *MockSMSService, *MockUserService)
		expectedStatus int
		expectedBody   map[string]interface{}
	}{
		{
			name: "successful OTP start",
			requestBody: models.OTPRequest{
				Phone: "+1234567890",
			},
			mockSetup: func(otpService *MockOTPService, smsService *MockSMSService, userService *MockUserService) {
				otpService.On("IsRateLimited", "+1234567890").Return(false, nil)
				otpService.On("GenerateAndStoreOTP", "+1234567890").Return("123456", nil)
				smsService.On("SendOTP", "+1234567890", "123456").Return(nil)
				otpService.On("IncrementRateLimit", "+1234567890").Return(nil)
			},
			expectedStatus: http.StatusOK,
			expectedBody: map[string]interface{}{
				"success": true,
				"message": "OTP sent successfully",
			},
		},
		{
			name: "rate limited",
			requestBody: models.OTPRequest{
				Phone: "+1234567890",
			},
			mockSetup: func(otpService *MockOTPService, smsService *MockSMSService, userService *MockUserService) {
				otpService.On("IsRateLimited", "+1234567890").Return(true, nil)
			},
			expectedStatus: http.StatusTooManyRequests,
			expectedBody: map[string]interface{}{
				"error":   "rate_limited",
				"message": "Too many OTP requests. Please try again later.",
			},
		},
		{
			name: "invalid phone number",
			requestBody: models.OTPRequest{
				Phone: "invalid",
			},
			mockSetup: func(otpService *MockOTPService, smsService *MockSMSService, userService *MockUserService) {
				// No mock calls expected for invalid phone
			},
			expectedStatus: http.StatusBadRequest,
			expectedBody: map[string]interface{}{
				"error":   "invalid_phone",
				"message": "Invalid phone number format",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock services
			mockOTPService := new(MockOTPService)
			mockSMSService := new(MockSMSService)
			mockUserService := new(MockUserService)

			// Setup mocks
			tt.mockSetup(mockOTPService, mockSMSService, mockUserService)

			// Create handler
			handler := NewAuthHandler(mockOTPService, mockSMSService, mockUserService)

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

			// Verify mocks were called
			mockOTPService.AssertExpectations(t)
			mockSMSService.AssertExpectations(t)
			mockUserService.AssertExpectations(t)
		})
	}
}

func TestAuthHandler_VerifyOTP(t *testing.T) {
	gin.SetMode(gin.TestMode)

	tests := []struct {
		name           string
		requestBody    models.OTPVerifyRequest
		mockSetup      func(*MockOTPService, *MockSMSService, *MockUserService)
		expectedStatus int
		expectedBody   map[string]interface{}
	}{
		{
			name: "successful OTP verification",
			requestBody: models.OTPVerifyRequest{
				Phone: "+1234567890",
				Code:  "123456",
			},
			mockSetup: func(otpService *MockOTPService, smsService *MockSMSService, userService *MockUserService) {
				otpService.On("VerifyOTP", "+1234567890", "123456").Return(true, nil)
				userService.On("CreateUser", "+1234567890").Return(&models.User{
					ID:        "user-123",
					PhoneE164: "+1234567890",
				}, nil)
			},
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
			mockSetup: func(otpService *MockOTPService, smsService *MockSMSService, userService *MockUserService) {
				otpService.On("VerifyOTP", "+1234567890", "000000").Return(false, assert.AnError)
			},
			expectedStatus: http.StatusBadRequest,
			expectedBody: map[string]interface{}{
				"error":   "otp_verification_error",
				"message": assert.AnError.Error(),
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create mock services
			mockOTPService := new(MockOTPService)
			mockSMSService := new(MockSMSService)
			mockUserService := new(MockUserService)

			// Setup mocks
			tt.mockSetup(mockOTPService, mockSMSService, mockUserService)

			// Create handler
			handler := NewAuthHandler(mockOTPService, mockSMSService, mockUserService)

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
				if key == "message" && expectedValue == assert.AnError.Error() {
					// For error messages, just check that the key exists
					assert.Contains(t, response, key)
				} else {
					assert.Equal(t, expectedValue, response[key])
				}
			}

			// Verify mocks were called
			mockOTPService.AssertExpectations(t)
			mockSMSService.AssertExpectations(t)
			mockUserService.AssertExpectations(t)
		})
	}
}
