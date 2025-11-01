package com.housing.payment.model.dto;

import com.housing.payment.model.Payment;
import com.housing.payment.model.PaymentStatus;
import com.housing.payment.model.PaymentType;
import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
public class PaymentResponse {
    private String id;
    private String userId;
    private String roomId;
    private BigDecimal amount;
    private String currency;
    private PaymentStatus status;
    private PaymentType type;
    private String description;
    private String stripePaymentIntentId;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    public static PaymentResponse fromPayment(Payment payment) {
        return PaymentResponse.builder()
                .id(payment.getId())
                .userId(payment.getUserId())
                .roomId(payment.getRoomId())
                .amount(payment.getAmount())
                .currency(payment.getCurrency())
                .status(payment.getStatus())
                .type(payment.getType())
                .description(payment.getDescription())
                .stripePaymentIntentId(payment.getStripePaymentIntentId())
                .createdAt(payment.getCreatedAt())
                .updatedAt(payment.getUpdatedAt())
                .build();
    }
}
