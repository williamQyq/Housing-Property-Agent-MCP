package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"identity/internal/models"
	"identity/internal/utils"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
)

type UserService struct {
	rdb    *redis.Client
	salt   string
}

func NewUserService(rdb *redis.Client) *UserService {
	return &UserService{
		rdb:  rdb,
		salt: "user-salt-key", // In production, use a proper salt from config
	}
}

func (s *UserService) CreateUser(phone string) (*models.User, error) {
	// Normalize phone number
	normalizedPhone, err := utils.NormalizePhone(phone)
	if err != nil {
		return nil, fmt.Errorf("invalid phone number: %w", err)
	}

	// Create phone hash for lookups
	phoneHash := utils.HashPhone(normalizedPhone, s.salt)

	// Check if user already exists
	existingUser, err := s.GetUserByPhoneHash(phoneHash)
	if err == nil && existingUser != nil {
		return existingUser, nil
	}

	// Create new user
	user := &models.User{
		ID:        uuid.New().String(),
		PhoneE164: normalizedPhone,
		PhoneHash: phoneHash,
		CreatedAt: time.Now(),
	}

	// Store user in Redis
	userKey := fmt.Sprintf("user:%s", user.ID)
	userHashKey := fmt.Sprintf("user_hash:%s", phoneHash)

	userData, err := json.Marshal(user)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal user: %w", err)
	}

	pipe := s.rdb.Pipeline()
	pipe.Set(context.Background(), userKey, userData, 0) // No expiry
	pipe.Set(context.Background(), userHashKey, user.ID, 0) // No expiry
	_, err = pipe.Exec(context.Background())

	if err != nil {
		return nil, fmt.Errorf("failed to store user: %w", err)
	}

	return user, nil
}

func (s *UserService) GetUserByID(userID string) (*models.User, error) {
	key := fmt.Sprintf("user:%s", userID)
	
	userData, err := s.rdb.Get(context.Background(), key).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	var user models.User
	err = json.Unmarshal([]byte(userData), &user)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal user: %w", err)
	}

	return &user, nil
}

func (s *UserService) GetUserByPhoneHash(phoneHash string) (*models.User, error) {
	// First get user ID by phone hash
	userIDKey := fmt.Sprintf("user_hash:%s", phoneHash)
	userID, err := s.rdb.Get(context.Background(), userIDKey).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, fmt.Errorf("user not found")
		}
		return nil, fmt.Errorf("failed to get user ID: %w", err)
	}

	// Then get user by ID
	return s.GetUserByID(userID)
}

func (s *UserService) GetUserByPhone(phone string) (*models.User, error) {
	// Normalize phone number
	normalizedPhone, err := utils.NormalizePhone(phone)
	if err != nil {
		return nil, fmt.Errorf("invalid phone number: %w", err)
	}

	// Create phone hash
	phoneHash := utils.HashPhone(normalizedPhone, s.salt)

	// Get user by phone hash
	return s.GetUserByPhoneHash(phoneHash)
}
