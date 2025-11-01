package com.housing.payment.service;

import com.housing.payment.model.Payment;
import com.housing.payment.model.PaymentStatus;
import com.housing.payment.model.PaymentType;
import com.housing.payment.model.dto.CreatePaymentRequest;
import com.housing.payment.model.dto.PaymentResponse;
import com.housing.payment.repository.PaymentRepository;
import com.stripe.Stripe;
import com.stripe.exception.StripeException;
import com.stripe.model.PaymentIntent;
import com.stripe.param.PaymentIntentCreateParams;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class PaymentService {

    private final PaymentRepository paymentRepository;

    @Value("${stripe.secret-key:sk_test_demo}")
    private String stripeSecretKey;

    @PostConstruct
    public void init() {
        Stripe.apiKey = stripeSecretKey;
    }

    @Transactional
    public PaymentResponse createPayment(CreatePaymentRequest request, String userId) {
        try {
            // Create Stripe PaymentIntent
            PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
                    .setAmount(request.getAmount().multiply(java.math.BigDecimal.valueOf(100)).longValue()) // Convert to cents
                    .setCurrency(request.getCurrency().toLowerCase())
                    .setDescription(request.getDescription())
                    .putMetadata("user_id", userId)
                    .putMetadata("room_id", request.getRoomId())
                    .putMetadata("type", request.getType().toString())
                    .build();

            PaymentIntent paymentIntent = PaymentIntent.create(params);

            // Create payment record
            Payment payment = Payment.builder()
                    .userId(userId)
                    .roomId(request.getRoomId())
                    .amount(request.getAmount())
                    .currency(request.getCurrency())
                    .status(PaymentStatus.PENDING)
                    .type(request.getType())
                    .description(request.getDescription())
                    .stripePaymentIntentId(paymentIntent.getId())
                    .build();

            Payment savedPayment = paymentRepository.save(payment);
            log.info("Created payment {} for user {} in room {}", savedPayment.getId(), userId, request.getRoomId());

            return PaymentResponse.fromPayment(savedPayment);

        } catch (StripeException e) {
            log.error("Failed to create Stripe PaymentIntent: {}", e.getMessage());
            throw new RuntimeException("Failed to create payment", e);
        }
    }

    @Transactional
    public PaymentResponse updatePaymentStatus(String paymentId, PaymentStatus status) {
        Optional<Payment> paymentOpt = paymentRepository.findById(paymentId);
        if (paymentOpt.isEmpty()) {
            throw new RuntimeException("Payment not found: " + paymentId);
        }

        Payment payment = paymentOpt.get();
        payment.setStatus(status);
        Payment updatedPayment = paymentRepository.save(payment);

        log.info("Updated payment {} status to {}", paymentId, status);
        return PaymentResponse.fromPayment(updatedPayment);
    }

    @Transactional
    public PaymentResponse confirmPayment(String paymentId) {
        Optional<Payment> paymentOpt = paymentRepository.findById(paymentId);
        if (paymentOpt.isEmpty()) {
            throw new RuntimeException("Payment not found: " + paymentId);
        }

        Payment payment = paymentOpt.get();
        
        try {
            // Retrieve and confirm the PaymentIntent from Stripe
            PaymentIntent paymentIntent = PaymentIntent.retrieve(payment.getStripePaymentIntentId());
            
            if (paymentIntent.getStatus().equals("succeeded")) {
                payment.setStatus(PaymentStatus.COMPLETED);
                payment.setStripeChargeId(paymentIntent.getLatestCharge());
            } else {
                payment.setStatus(PaymentStatus.FAILED);
            }
            
            Payment updatedPayment = paymentRepository.save(payment);
            log.info("Confirmed payment {} with status {}", paymentId, updatedPayment.getStatus());
            
            return PaymentResponse.fromPayment(updatedPayment);
            
        } catch (StripeException e) {
            log.error("Failed to confirm payment {}: {}", paymentId, e.getMessage());
            payment.setStatus(PaymentStatus.FAILED);
            Payment updatedPayment = paymentRepository.save(payment);
            return PaymentResponse.fromPayment(updatedPayment);
        }
    }

    public List<PaymentResponse> getPaymentsByUser(String userId) {
        List<Payment> payments = paymentRepository.findByUserId(userId);
        return payments.stream()
                .map(PaymentResponse::fromPayment)
                .collect(Collectors.toList());
    }

    public List<PaymentResponse> getPaymentsByRoom(String roomId) {
        List<Payment> payments = paymentRepository.findByRoomId(roomId);
        return payments.stream()
                .map(PaymentResponse::fromPayment)
                .collect(Collectors.toList());
    }

    public List<PaymentResponse> getPaymentsByUserAndRoom(String userId, String roomId) {
        List<Payment> payments = paymentRepository.findByUserIdAndRoomId(userId, roomId);
        return payments.stream()
                .map(PaymentResponse::fromPayment)
                .collect(Collectors.toList());
    }

    public PaymentResponse getPaymentById(String paymentId) {
        Optional<Payment> payment = paymentRepository.findById(paymentId);
        if (payment.isEmpty()) {
            throw new RuntimeException("Payment not found: " + paymentId);
        }
        return PaymentResponse.fromPayment(payment.get());
    }

    @Transactional
    public PaymentResponse refundPayment(String paymentId) {
        Optional<Payment> paymentOpt = paymentRepository.findById(paymentId);
        if (paymentOpt.isEmpty()) {
            throw new RuntimeException("Payment not found: " + paymentId);
        }

        Payment payment = paymentOpt.get();
        
        if (payment.getStatus() != PaymentStatus.COMPLETED) {
            throw new RuntimeException("Only completed payments can be refunded");
        }

        try {
            // Create refund in Stripe
            com.stripe.model.Refund refund = com.stripe.model.Refund.create(
                    com.stripe.param.RefundCreateParams.builder()
                            .setCharge(payment.getStripeChargeId())
                            .build()
            );

            payment.setStatus(PaymentStatus.REFUNDED);
            Payment updatedPayment = paymentRepository.save(payment);
            
            log.info("Refunded payment {} with refund ID {}", paymentId, refund.getId());
            return PaymentResponse.fromPayment(updatedPayment);
            
        } catch (StripeException e) {
            log.error("Failed to refund payment {}: {}", paymentId, e.getMessage());
            throw new RuntimeException("Failed to refund payment", e);
        }
    }
}
