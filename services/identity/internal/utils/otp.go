package utils

import (
	"crypto/rand"
	"fmt"
	"math/big"
)

// GenerateOTP generates a 6-digit OTP code
func GenerateOTP() (string, error) {
	// Generate a random 6-digit number
	max := big.NewInt(999999)
	min := big.NewInt(100000)
	
	n, err := rand.Int(rand.Reader, new(big.Int).Sub(max, min))
	if err != nil {
		return "", err
	}
	
	otp := new(big.Int).Add(n, min)
	return fmt.Sprintf("%06d", otp.Int64()), nil
}

// ValidateOTP validates that the OTP is a 6-digit number
func ValidateOTP(code string) bool {
	if len(code) != 6 {
		return false
	}
	
	for _, char := range code {
		if char < '0' || char > '9' {
			return false
		}
	}
	
	return true
}
