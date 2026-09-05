"""
Tests for Subscription Model
Test-driven development for professional subscription functionality.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from models.subscription import Subscription, PaymentMethod, UsageRecord, Invoice
from models.user import User
from db import get_db


class TestSubscriptionModel:
    """Test subscription model functionality."""
    
    def test_create_subscription(self, db_session: Session):
        """Test creating a new subscription."""
        # Create a user first
        user = User(
            email="test@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Create subscription
        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            status="active",
            stripe_subscription_id="sub_test123",
            stripe_customer_id="cus_test123",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        
        db_session.add(subscription)
        db_session.commit()
        
        # Verify subscription was created
        assert subscription.id is not None
        assert subscription.user_id == user.id
        assert subscription.plan == "pro"
        assert subscription.status == "active"
        assert subscription.created_at is not None
    
    def test_subscription_plan_types(self, db_session: Session):
        """Test different subscription plan types."""
        user = User(
            email="plans@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        plans = ["free", "pro", "enterprise"]
        
        for plan in plans:
            subscription = Subscription(
                user_id=user.id,
                plan=plan,
                status="active",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            db_session.add(subscription)
        
        db_session.commit()
        
        # Verify all plans were created
        subscriptions = db_session.query(Subscription).filter(
            Subscription.user_id == user.id
        ).all()
        
        assert len(subscriptions) == 3
        created_plans = [sub.plan for sub in subscriptions]
        assert all(plan in created_plans for plan in plans)
    
    def test_subscription_cancellation(self, db_session: Session):
        """Test subscription cancellation workflow."""
        user = User(
            email="cancel@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Cancel subscription
        subscription.status = "canceled"
        subscription.cancel_at_period_end = True
        subscription.canceled_at = datetime.utcnow()
        db_session.commit()
        
        # Verify cancellation
        assert subscription.status == "canceled"
        assert subscription.cancel_at_period_end is True
        assert subscription.canceled_at is not None


class TestPaymentMethodModel:
    """Test payment method model functionality."""
    
    def test_create_payment_method(self, db_session: Session):
        """Test creating a payment method."""
        # Create user and subscription
        user = User(
            email="payment@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Create payment method
        payment_method = PaymentMethod(
            subscription_id=subscription.id,
            stripe_payment_method_id="pm_test123",
            type="card",
            last_four="4242",
            brand="visa",
            is_default=True
        )
        
        db_session.add(payment_method)
        db_session.commit()
        
        # Verify payment method
        assert payment_method.id is not None
        assert payment_method.subscription_id == subscription.id
        assert payment_method.type == "card"
        assert payment_method.last_four == "4242"
        assert payment_method.brand == "visa"
        assert payment_method.is_default is True


class TestUsageRecordModel:
    """Test usage tracking model."""
    
    def test_create_usage_record(self, db_session: Session):
        """Test creating usage records for billing."""
        user = User(
            email="usage@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Create usage record
        usage_record = UsageRecord(
            user_id=user.id,
            metric_name="quizzes_generated",
            quantity=5,
            billing_period_start=datetime.utcnow().replace(day=1),
            billing_period_end=datetime.utcnow().replace(day=28),
            properties='{"topic": "Science", "difficulty": "medium"}'
        )
        
        db_session.add(usage_record)
        db_session.commit()
        
        # Verify usage record
        assert usage_record.id is not None
        assert usage_record.user_id == user.id
        assert usage_record.metric_name == "quizzes_generated"
        assert usage_record.quantity == 5
        assert usage_record.properties is not None


class TestInvoiceModel:
    """Test invoice model functionality."""
    
    def test_create_invoice(self, db_session: Session):
        """Test creating invoices."""
        # Create user and subscription
        user = User(
            email="invoice@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        # Create invoice
        invoice = Invoice(
            user_id=user.id,
            subscription_id=subscription.id,
            invoice_number="INV-2024-001",
            amount_due=Decimal("19.99"),
            amount_paid=Decimal("19.99"),
            currency="USD",
            status="paid",
            stripe_invoice_id="in_test123",
            issue_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            paid_at=datetime.utcnow(),
            description="Pro Plan - Monthly Subscription"
        )
        
        db_session.add(invoice)
        db_session.commit()
        
        # Verify invoice
        assert invoice.id is not None
        assert invoice.user_id == user.id
        assert invoice.subscription_id == subscription.id
        assert invoice.invoice_number == "INV-2024-001"
        assert invoice.amount_due == Decimal("19.99")
        assert invoice.amount_paid == Decimal("19.99")
        assert invoice.status == "paid" 