package com.housing.payment.controller;

import com.housing.payment.model.PaymentStatus;
import com.housing.payment.model.dto.CreatePaymentRequest;
import com.housing.payment.model.dto.PaymentResponse;
import com.housing.payment.service.PaymentService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/payments")
@RequiredArgsConstructor
@Slf4j
public class PaymentController {

    private final PaymentService paymentService;

    @PostMapping
    public ResponseEntity<PaymentResponse> createPayment(
            @Valid @RequestBody CreatePaymentRequest request,
            @RequestHeader("X-User-ID") String userId) {
        
        log.info("Creating payment for user {} in room {}", userId, request.getRoomId());
        PaymentResponse payment = paymentService.createPayment(request, userId);
        return ResponseEntity.status(HttpStatus.CREATED).body(payment);
    }

    @GetMapping("/{paymentId}")
    public ResponseEntity<PaymentResponse> getPayment(@PathVariable String paymentId) {
        PaymentResponse payment = paymentService.getPaymentById(paymentId);
        return ResponseEntity.ok(payment);
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<List<PaymentResponse>> getPaymentsByUser(@PathVariable String userId) {
        List<PaymentResponse> payments = paymentService.getPaymentsByUser(userId);
        return ResponseEntity.ok(payments);
    }

    @GetMapping("/room/{roomId}")
    public ResponseEntity<List<PaymentResponse>> getPaymentsByRoom(@PathVariable String roomId) {
        List<PaymentResponse> payments = paymentService.getPaymentsByRoom(roomId);
        return ResponseEntity.ok(payments);
    }

    @GetMapping("/user/{userId}/room/{roomId}")
    public ResponseEntity<List<PaymentResponse>> getPaymentsByUserAndRoom(
            @PathVariable String userId,
            @PathVariable String roomId) {
        List<PaymentResponse> payments = paymentService.getPaymentsByUserAndRoom(userId, roomId);
        return ResponseEntity.ok(payments);
    }

    @PostMapping("/{paymentId}/confirm")
    public ResponseEntity<PaymentResponse> confirmPayment(@PathVariable String paymentId) {
        log.info("Confirming payment {}", paymentId);
        PaymentResponse payment = paymentService.confirmPayment(paymentId);
        return ResponseEntity.ok(payment);
    }

    @PostMapping("/{paymentId}/refund")
    public ResponseEntity<PaymentResponse> refundPayment(@PathVariable String paymentId) {
        log.info("Refunding payment {}", paymentId);
        PaymentResponse payment = paymentService.refundPayment(paymentId);
        return ResponseEntity.ok(payment);
    }

    @PutMapping("/{paymentId}/status")
    public ResponseEntity<PaymentResponse> updatePaymentStatus(
            @PathVariable String paymentId,
            @RequestParam PaymentStatus status) {
        log.info("Updating payment {} status to {}", paymentId, status);
        PaymentResponse payment = paymentService.updatePaymentStatus(paymentId, status);
        return ResponseEntity.ok(payment);
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Payment service is healthy");
    }
}
