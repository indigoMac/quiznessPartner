"""
Subscription and Payment Models for QuizNess Professional Platform
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from models.base import Base


class Subscription(Base):
    """User subscription model for different tiers."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan = Column(String(50), nullable=False)  # free, pro, enterprise
    status = Column(String(50), nullable=False)  # active, canceled, past_due
    
    # Stripe integration
    stripe_subscription_id = Column(String(255), unique=True, nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # Billing periods
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    
    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payment_methods = relationship("PaymentMethod", back_populates="subscription")


class PaymentMethod(Base):
    """Payment methods for users."""
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    
    # Stripe payment method info
    stripe_payment_method_id = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # card, bank_account
    
    # Card details (last 4 digits, brand)
    last_four = Column(String(4), nullable=True)
    brand = Column(String(50), nullable=True)
    
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payment_methods")


class UsageRecord(Base):
    """Track usage for billing and analytics."""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Usage metrics
    metric_name = Column(String(100), nullable=False)  # quizzes_generated, questions_created
    quantity = Column(Integer, nullable=False, default=1)
    
    # Billing period
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    
    # Metadata
    properties = Column(Text, nullable=True)  # JSON string for additional data
    recorded_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    """Invoice records for transparent billing."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    
    # Invoice details
    invoice_number = Column(String(100), unique=True, nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    currency = Column(String(3), default="USD")
    
    # Status
    status = Column(String(50), nullable=False)  # draft, open, paid, void
    
    # Stripe integration
    stripe_invoice_id = Column(String(255), unique=True, nullable=True)
    
    # Dates
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 