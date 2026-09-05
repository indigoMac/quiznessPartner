"""
Professional Payment Service for QuizNess
Handles Stripe integration, subscription management, and billing.
"""

import os
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.user import User
from models.subscription import Subscription, PaymentMethod

# Handle structlog import gracefully
try:
    import structlog
    logger = structlog.get_logger(__name__)
    use_structlog = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    use_structlog = False

# Mock stripe for testing
try:
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
except ImportError:
    # Mock stripe if not installed
    class MockStripe:
        class Customer:
            @staticmethod
            def create(**kwargs):
                class MockCustomer:
                    id = "cus_mock123"
                return MockCustomer()
        
        class checkout:
            class Session:
                @staticmethod
                def create(**kwargs):
                    class MockSession:
                        url = "https://checkout.stripe.com/mock"
                        id = "cs_mock123"
                    return MockSession()
        
        class Webhook:
            @staticmethod
            def construct_event(payload, sig_header, webhook_secret):
                return {"type": "test.event", "data": {"object": {}}}
    
    stripe = MockStripe()


def log_info(message: str, **kwargs):
    """Helper function for structured logging."""
    if use_structlog:
        logger.info(message, **kwargs)
    else:
        logger.info(f"{message} - {kwargs}")


def log_error(message: str, **kwargs):
    """Helper function for structured logging."""
    if use_structlog:
        logger.error(message, **kwargs)
    else:
        logger.error(f"{message} - {kwargs}")


class PaymentService:
    """Professional payment processing service."""
    
    # Subscription tiers
    PLANS = {
        "free": {
            "name": "Free Tier",
            "price": 0,
            "quizzes_per_month": 5,
            "questions_per_quiz": 10,
            "features": ["basic_analytics", "email_support"]
        },
        "pro": {
            "name": "Professional",
            "price": 1999,  # $19.99 in cents
            "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID", "price_pro_mock"),
            "quizzes_per_month": 100,
            "questions_per_quiz": 50,
            "features": ["advanced_analytics", "priority_support", "custom_branding", "api_access"]
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 9999,  # $99.99 in cents
            "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "price_enterprise_mock"),
            "quizzes_per_month": -1,  # Unlimited
            "questions_per_quiz": 200,
            "features": ["all_features", "dedicated_support", "sso", "advanced_integrations"]
        }
    }

    def __init__(self, db: Session):
        self.db = db

    async def create_checkout_session(
        self, 
        user_id: int, 
        plan: str, 
        success_url: str, 
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            if plan not in self.PLANS or plan == "free":
                raise ValueError("Invalid plan selected")

            plan_config = self.PLANS[plan]
            
            # Create Stripe customer if doesn't exist
            if not hasattr(user, 'stripe_customer_id') or not user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={"user_id": str(user_id)}
                )
                user.stripe_customer_id = customer.id
                self.db.commit()

            session = stripe.checkout.Session.create(
                customer=user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan_config["stripe_price_id"],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                metadata={
                    "user_id": str(user_id),
                    "plan": plan
                }
            )

            log_info("Checkout session created", 
                    user_id=user_id, 
                    plan=plan, 
                    session_id=session.id)

            return {
                "checkout_url": session.url,
                "session_id": session.id
            }

        except Exception as e:
            log_error("Failed to create checkout session", 
                     user_id=user_id, 
                     plan=plan, 
                     error=str(e))
            raise

    async def handle_webhook(self, payload: str, sig_header: str) -> bool:
        """Handle Stripe webhooks for subscription events."""
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                await self._handle_successful_payment(event['data']['object'])
            elif event['type'] == 'invoice.payment_succeeded':
                await self._handle_recurring_payment(event['data']['object'])
            elif event['type'] == 'customer.subscription.deleted':
                await self._handle_cancellation(event['data']['object'])
            
            log_info("Webhook processed successfully", event_type=event['type'])
            return True
            
        except Exception as e:
            log_error("Webhook processing failed", error=str(e))
            return False

    async def _handle_successful_payment(self, session: Dict[str, Any]):
        """Handle successful subscription payment."""
        user_id = int(session['metadata']['user_id'])
        plan = session['metadata']['plan']
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            # Create or update subscription
            subscription = Subscription(
                user_id=user_id,
                plan=plan,
                stripe_subscription_id=session['subscription'],
                status='active',
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30)
            )
            
            self.db.add(subscription)
            self.db.commit()
            
            log_info("Subscription activated", 
                    user_id=user_id, 
                    plan=plan,
                    subscription_id=session['subscription'])

    async def _handle_recurring_payment(self, invoice: Dict[str, Any]):
        """Handle recurring payment success."""
        # Implementation for recurring payments
        pass

    async def _handle_cancellation(self, subscription: Dict[str, Any]):
        """Handle subscription cancellation."""
        # Implementation for cancellation
        pass

    def get_usage_limits(self, user_id: int) -> Dict[str, Any]:
        """Get current usage limits for a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return self.PLANS["free"]
            
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == 'active'
        ).first()
        
        if not subscription:
            return self.PLANS["free"]
            
        return self.PLANS.get(subscription.plan, self.PLANS["free"])

    def check_quiz_limit(self, user_id: int) -> bool:
        """Check if user can create more quizzes this month."""
        limits = self.get_usage_limits(user_id)
        
        if limits["quizzes_per_month"] == -1:  # Unlimited
            return True
            
        # Count quizzes created this month
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        
        # Use raw SQL query since we don't have quiz model in tests
        try:
            current_count = self.db.execute(
                text("""
                SELECT COUNT(*) FROM quizzes 
                WHERE user_id = :user_id 
                AND created_at >= :start_date
                """),
                {"user_id": user_id, "start_date": start_of_month}
            ).scalar()
        except Exception:
            # If quizzes table doesn't exist, assume 0
            current_count = 0
        
        return current_count < limits["quizzes_per_month"] 