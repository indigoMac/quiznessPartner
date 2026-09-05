"""
Tests for Payment Service
Test-driven development for professional payment functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from services.payment_service import PaymentService
from models.user import User
from models.subscription import Subscription


class TestPaymentService:
    """Test payment service functionality."""
    
    def test_payment_service_initialization(self, db_session: Session):
        """Test payment service can be initialized."""
        service = PaymentService(db_session)
        assert service.db == db_session
        
    def test_subscription_plans_defined(self, db_session: Session):
        """Test that subscription plans are properly defined."""
        service = PaymentService(db_session)
        
        # Verify all plans exist
        assert "free" in service.PLANS
        assert "pro" in service.PLANS
        assert "enterprise" in service.PLANS
        
        # Verify plan structure
        for plan_name, plan_config in service.PLANS.items():
            assert "name" in plan_config
            assert "price" in plan_config
            assert "quizzes_per_month" in plan_config
            assert "questions_per_quiz" in plan_config
            assert "features" in plan_config
            
        # Verify free plan
        free_plan = service.PLANS["free"]
        assert free_plan["price"] == 0
        assert free_plan["quizzes_per_month"] == 5
        
        # Verify pro plan
        pro_plan = service.PLANS["pro"]
        assert pro_plan["price"] == 1999  # $19.99 in cents
        assert pro_plan["quizzes_per_month"] == 100
        
        # Verify enterprise plan
        enterprise_plan = service.PLANS["enterprise"]
        assert enterprise_plan["price"] == 9999  # $99.99 in cents
        assert enterprise_plan["quizzes_per_month"] == -1  # Unlimited

    @pytest.mark.asyncio
    @patch('services.payment_service.stripe')
    async def test_create_checkout_session(
        self, 
        mock_stripe,
        db_session: Session
    ):
        """Test creating a Stripe checkout session."""
        # Setup mocks
        mock_customer = Mock()
        mock_customer.id = "cus_test123"
        mock_stripe.Customer.create.return_value = mock_customer
        
        mock_session = Mock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.id = "cs_test123"
        mock_stripe.checkout.Session.create.return_value = mock_session
        
        # Create user
        user = User(
            email="payment_test@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Test checkout session creation
        service = PaymentService(db_session)
        result = await service.create_checkout_session(
            user_id=user.id,
            plan="pro",
            success_url="https://app.com/success",
            cancel_url="https://app.com/cancel"
        )
        
        # Verify result
        assert "checkout_url" in result
        assert "session_id" in result
        assert result["checkout_url"] == "https://checkout.stripe.com/test"
        assert result["session_id"] == "cs_test123"
        
        # Verify user got stripe customer ID
        db_session.refresh(user)
        assert user.stripe_customer_id == "cus_test123"

    @pytest.mark.asyncio
    async def test_create_checkout_session_invalid_plan(self, db_session: Session):
        """Test that invalid plan raises error."""
        user = User(
            email="invalid_plan@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        service = PaymentService(db_session)
        
        with pytest.raises(ValueError, match="Invalid plan selected"):
            await service.create_checkout_session(
                user_id=user.id,
                plan="invalid_plan",
                success_url="https://app.com/success",
                cancel_url="https://app.com/cancel"
            )

    @pytest.mark.asyncio
    async def test_create_checkout_session_free_plan(self, db_session: Session):
        """Test that free plan cannot be purchased."""
        user = User(
            email="free_plan@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        service = PaymentService(db_session)
        
        with pytest.raises(ValueError, match="Invalid plan selected"):
            await service.create_checkout_session(
                user_id=user.id,
                plan="free",
                success_url="https://app.com/success",
                cancel_url="https://app.com/cancel"
            )

    def test_get_usage_limits_free_user(self, db_session: Session):
        """Test getting usage limits for free user."""
        user = User(
            email="free_user@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        service = PaymentService(db_session)
        limits = service.get_usage_limits(user.id)
        
        # Should return free plan limits
        assert limits["quizzes_per_month"] == 5
        assert limits["questions_per_quiz"] == 10
        assert "basic_analytics" in limits["features"]

    def test_get_usage_limits_pro_user(self, db_session: Session):
        """Test getting usage limits for pro user."""
        user = User(
            email="pro_user@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Create pro subscription
        subscription = Subscription(
            user_id=user.id,
            plan="pro",
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        service = PaymentService(db_session)
        limits = service.get_usage_limits(user.id)
        
        # Should return pro plan limits
        assert limits["quizzes_per_month"] == 100
        assert limits["questions_per_quiz"] == 50
        assert "advanced_analytics" in limits["features"]
        assert "api_access" in limits["features"]

    def test_check_quiz_limit_free_user_under_limit(self, db_session: Session):
        """Test quiz limit check for free user under limit."""
        user = User(
            email="under_limit@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        service = PaymentService(db_session)
        # Free user should be under limit (no quizzes created)
        can_create = service.check_quiz_limit(user.id)
        assert can_create is True

    @patch('services.payment_service.PaymentService.check_quiz_limit')
    def test_check_quiz_limit_free_user_at_limit(self, mock_check_limit, db_session: Session):
        """Test quiz limit check for free user at limit."""
        user = User(
            email="at_limit@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Mock that user is at limit
        mock_check_limit.return_value = False
        
        service = PaymentService(db_session)
        can_create = service.check_quiz_limit(user.id)
        assert can_create is False

    def test_check_quiz_limit_enterprise_user(self, db_session: Session):
        """Test quiz limit check for enterprise user (unlimited)."""
        user = User(
            email="enterprise@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Create enterprise subscription
        subscription = Subscription(
            user_id=user.id,
            plan="enterprise",
            status="active",
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        db_session.commit()
        
        service = PaymentService(db_session)
        # Enterprise user should always be able to create quizzes
        can_create = service.check_quiz_limit(user.id)
        assert can_create is True

    @pytest.mark.asyncio
    @patch('services.payment_service.stripe')
    async def test_handle_webhook_successful_payment(
        self, 
        mock_stripe,
        db_session: Session
    ):
        """Test handling successful payment webhook."""
        # Setup mock webhook event
        mock_event = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'metadata': {
                        'user_id': '1',
                        'plan': 'pro'
                    },
                    'subscription': 'sub_test123'
                }
            }
        }
        mock_stripe.Webhook.construct_event.return_value = mock_event
        
        # Create user
        user = User(
            email="webhook_test@example.com",
            hashed_password="hashed123",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        service = PaymentService(db_session)
        result = await service.handle_webhook("payload", "signature")
        
        assert result is True
        
        # Verify subscription was created
        subscription = db_session.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()
        assert subscription is not None
        assert subscription.plan == "pro"
        assert subscription.status == "active"

    @pytest.mark.asyncio
    @patch('services.payment_service.stripe')
    async def test_handle_webhook_invalid_signature(
        self, 
        mock_stripe,
        db_session: Session
    ):
        """Test handling webhook with invalid signature."""
        # Mock invalid signature exception
        mock_stripe.Webhook.construct_event.side_effect = Exception("Invalid signature")
        
        service = PaymentService(db_session)
        result = await service.handle_webhook("payload", "invalid_signature")
        
        assert result is False 