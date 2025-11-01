package services

import (
	"fmt"
	"log"

	"github.com/twilio/twilio-go"
	twilioApi "github.com/twilio/twilio-go/rest/api/v2010"
)

type SMSService struct {
	client        *twilio.RestClient
	fromNumber    string
}

func NewSMSService(accountSID, authToken, fromNumber string) *SMSService {
	client := twilio.NewRestClientWithParams(twilio.ClientParams{
		Username: accountSID,
		Password: authToken,
	})

	return &SMSService{
		client:     client,
		fromNumber: fromNumber,
	}
}

func (s *SMSService) SendOTP(phone, code string) error {
	// In development mode, just log the OTP
	if s.fromNumber == "" {
		log.Printf("SMS OTP for %s: %s", phone, code)
		return nil
	}

	message := fmt.Sprintf("Your verification code is: %s. This code will expire in 5 minutes.", code)

	params := &twilioApi.CreateMessageParams{}
	params.SetTo(phone)
	params.SetFrom(s.fromNumber)
	params.SetBody(message)

	_, err := s.client.Api.CreateMessage(params)
	if err != nil {
		return fmt.Errorf("failed to send SMS: %w", err)
	}

	return nil
}

func (s *SMSService) SendInvite(phone, inviteLink string) error {
	// In development mode, just log the invite
	if s.fromNumber == "" {
		log.Printf("Invite SMS for %s: %s", phone, inviteLink)
		return nil
	}

	message := fmt.Sprintf("You've been invited to join a room! Click here to accept: %s", inviteLink)

	params := &twilioApi.CreateMessageParams{}
	params.SetTo(phone)
	params.SetFrom(s.fromNumber)
	params.SetBody(message)

	_, err := s.client.Api.CreateMessage(params)
	if err != nil {
		return fmt.Errorf("failed to send invite SMS: %w", err)
	}

	return nil
}
