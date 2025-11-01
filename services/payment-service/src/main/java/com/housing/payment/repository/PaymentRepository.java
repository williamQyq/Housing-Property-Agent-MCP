package com.housing.payment.repository;

import com.housing.payment.model.Payment;
import com.housing.payment.model.PaymentStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PaymentRepository extends JpaRepository<Payment, String> {
    
    List<Payment> findByUserIdAndRoomId(String userId, String roomId);
    
    List<Payment> findByUserId(String userId);
    
    List<Payment> findByRoomId(String roomId);
    
    List<Payment> findByStatus(PaymentStatus status);
    
    @Query("SELECT p FROM Payment p WHERE p.userId = :userId AND p.status = :status")
    List<Payment> findByUserIdAndStatus(@Param("userId") String userId, @Param("status") PaymentStatus status);
    
    Optional<Payment> findByStripePaymentIntentId(String stripePaymentIntentId);
    
    Optional<Payment> findByStripeChargeId(String stripeChargeId);
}
