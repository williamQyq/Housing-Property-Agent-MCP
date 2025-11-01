package utils

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"regexp"
	"strings"
)

// NormalizePhone normalizes a phone number to E.164 format
func NormalizePhone(phone string) (string, error) {
	// Remove all non-digit characters
	re := regexp.MustCompile(`\D`)
	digits := re.ReplaceAllString(phone, "")

	// Handle different formats
	if len(digits) == 10 {
		// US number without country code
		return "+1" + digits, nil
	} else if len(digits) == 11 && digits[0] == '1' {
		// US number with country code
		return "+" + digits, nil
	} else if len(digits) > 11 {
		// International number
		return "+" + digits, nil
	}

	return "", fmt.Errorf("invalid phone number format: %s", phone)
}

// HashPhone creates a SHA-256 hash of the phone number for lookups
func HashPhone(phone string, salt string) string {
	hash := sha256.Sum256([]byte(phone + salt))
	return hex.EncodeToString(hash[:])
}

// MaskPhone masks a phone number for display (e.g., +1234567890 -> +1234***7890)
func MaskPhone(phone string) string {
	if len(phone) < 8 {
		return phone
	}
	
	// Keep first 4 and last 4 characters, mask the middle
	start := phone[:4]
	end := phone[len(phone)-4:]
	middle := strings.Repeat("*", len(phone)-8)
	
	return start + middle + end
}
