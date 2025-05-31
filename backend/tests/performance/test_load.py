"""
Performance Tests for QuizNess Backend using Locust

Tests application performance under various load conditions:
- User registration and authentication load
- Quiz creation performance
- Quiz taking and submission load
- Concurrent user scenarios
"""

from locust import HttpUser, task, between, events
import json
import random
import string
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizNessUser(HttpUser):
    """
    Simulates a typical QuizNess user workflow
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts - handles registration and login"""
        self.register_and_login()
    
    def register_and_login(self):
        """Register a new user and login to get authentication token"""
        # Generate unique user data
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.email = f"loadtest_{random_suffix}@example.com"
        self.password = "LoadTest123!"
        self.full_name = f"Load Test User {random_suffix}"
        
        # Register user
        user_data = {
            "email": self.email,
            "password": self.password,
            "full_name": self.full_name
        }
        
        with self.client.post("/auth/register", json=user_data, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
                logger.info(f"User {self.email} registered successfully")
            else:
                response.failure(f"Registration failed: {response.text}")
                return
        
        # Login to get token
        login_data = {
            "username": self.email,
            "password": self.password
        }
        
        with self.client.post("/auth/login", data=login_data, catch_response=True) as response:
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
                logger.info(f"User {self.email} logged in successfully")
            else:
                response.failure(f"Login failed: {response.text}")
    
    @task(3)
    def create_quiz(self):
        """Create a quiz from text - most common operation"""
        quiz_texts = [
            "Python is a high-level programming language known for its simplicity and readability.",
            "Machine learning is a subset of artificial intelligence that focuses on algorithms.",
            "Web development involves creating websites and web applications using various technologies.",
            "Database management systems are software applications that interact with databases.",
            "Cloud computing provides on-demand access to computing resources over the internet."
        ]
        
        quiz_data = {
            "text": random.choice(quiz_texts),
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "num_questions": random.randint(3, 8)
        }
        
        with self.client.post("/generate-quiz", json=quiz_data, headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                quiz = response.json()
                self.last_quiz_id = quiz.get("id")
                response.success()
                logger.debug(f"Quiz created: {quiz.get('title')}")
            else:
                response.failure(f"Quiz creation failed: {response.text}")
    
    @task(2)
    def get_quiz(self):
        """Retrieve a quiz for taking"""
        if hasattr(self, 'last_quiz_id') and self.last_quiz_id:
            with self.client.get(f"/quiz/{self.last_quiz_id}", headers=self.headers, catch_response=True) as response:
                if response.status_code == 200:
                    quiz = response.json()
                    self.current_quiz = quiz
                    response.success()
                    logger.debug(f"Retrieved quiz: {quiz.get('title')}")
                else:
                    response.failure(f"Quiz retrieval failed: {response.text}")
    
    @task(2)
    def submit_quiz_answers(self):
        """Submit answers to a quiz"""
        if hasattr(self, 'current_quiz') and self.current_quiz:
            questions = self.current_quiz.get("questions", [])
            if questions:
                # Generate random answers
                answers = []
                for question in questions:
                    if question.get("type") == "multiple_choice":
                        options_count = len(question.get("options", []))
                        if options_count > 0:
                            answers.append(random.randint(0, options_count - 1))
                        else:
                            answers.append(0)
                    else:
                        answers.append(0)
                
                submission_data = {
                    "quiz_id": self.current_quiz["id"],
                    "answers": answers
                }
                
                with self.client.post("/submit-answers", json=submission_data, headers=self.headers, catch_response=True) as response:
                    if response.status_code == 200:
                        result = response.json()
                        response.success()
                        logger.debug(f"Quiz submitted, score: {result.get('score', 0)}%")
                    else:
                        response.failure(f"Answer submission failed: {response.text}")
    
    @task(1)
    def upload_document(self):
        """Upload a document to create a quiz"""
        # Create a mock document
        document_content = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create 
        intelligent machines that work and react like humans. Some of the activities 
        computers with artificial intelligence are designed for include speech recognition, 
        learning, planning, and problem solving.
        """
        
        files = {"file": ("test_document.txt", document_content.encode(), "text/plain")}
        
        with self.client.post("/upload-document", files=files, headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                quiz = response.json()
                self.last_quiz_id = quiz.get("id")
                response.success()
                logger.debug(f"Document uploaded and quiz created: {quiz.get('title')}")
            else:
                response.failure(f"Document upload failed: {response.text}")
    
    @task(1)
    def check_health(self):
        """Check application health"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.text}")
    
    @task(1)
    def get_user_profile(self):
        """Get current user profile"""
        with self.client.get("/auth/me", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                profile = response.json()
                response.success()
                logger.debug(f"Profile retrieved for: {profile.get('email')}")
            else:
                response.failure(f"Profile retrieval failed: {response.text}")


class HeavyQuizUser(HttpUser):
    """
    Simulates users creating large, complex quizzes
    """
    wait_time = between(2, 5)
    
    def on_start(self):
        """Register and login"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.email = f"heavy_{random_suffix}@example.com"
        self.password = "HeavyTest123!"
        
        # Register
        user_data = {
            "email": self.email,
            "password": self.password,
            "full_name": f"Heavy User {random_suffix}"
        }
        self.client.post("/auth/register", json=user_data)
        
        # Login
        login_data = {"username": self.email, "password": self.password}
        response = self.client.post("/auth/login", data=login_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task
    def create_large_quiz(self):
        """Create quizzes with many questions"""
        large_text = """
        Machine Learning is a subset of artificial intelligence (AI) that provides systems 
        the ability to automatically learn and improve from experience without being explicitly 
        programmed. Machine learning focuses on the development of computer programs that can 
        access data and use it to learn for themselves. The process of learning begins with 
        observations or data, such as examples, direct experience, or instruction, in order 
        to look for patterns in data and make better decisions in the future based on the 
        examples that we provide. The primary aim is to allow the computers learn automatically 
        without human intervention or assistance and adjust actions accordingly.
        
        Some machine learning methods include supervised learning, unsupervised learning, 
        and reinforcement learning. Supervised learning algorithms build a mathematical model 
        of a set of data that contains both the inputs and the desired outputs. Unsupervised 
        learning algorithms take a set of data that contains only inputs, and find structure 
        in the data, like grouping or clustering of data points. Reinforcement learning is 
        an area of machine learning concerned with how software agents ought to take actions 
        in an environment in order to maximize the notion of cumulative reward.
        """
        
        quiz_data = {
            "text": large_text,
            "difficulty": "hard",
            "num_questions": 15  # Large number of questions
        }
        
        with self.client.post("/generate-quiz", json=quiz_data, headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Large quiz creation failed: {response.text}")


class BurstUser(HttpUser):
    """
    Simulates burst traffic patterns
    """
    wait_time = between(0.1, 0.5)  # Very short wait times
    
    def on_start(self):
        """Quick registration and login"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.email = f"burst_{random_suffix}@example.com"
        self.password = "BurstTest123!"
        
        # Register and login quickly
        user_data = {
            "email": self.email,
            "password": self.password,
            "full_name": f"Burst User {random_suffix}"
        }
        self.client.post("/auth/register", json=user_data)
        
        login_data = {"username": self.email, "password": self.password}
        response = self.client.post("/auth/login", data=login_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(5)
    def rapid_quiz_creation(self):
        """Rapidly create simple quizzes"""
        simple_texts = [
            "Python is a programming language.",
            "JavaScript runs in browsers.",
            "SQL is used for databases.",
            "HTML structures web pages.",
            "CSS styles web pages."
        ]
        
        quiz_data = {
            "text": random.choice(simple_texts),
            "difficulty": "easy",
            "num_questions": 3
        }
        
        self.client.post("/generate-quiz", json=quiz_data, headers=self.headers)
    
    @task(3)
    def rapid_health_checks(self):
        """Rapid health check requests"""
        self.client.get("/health")


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Custom request handler for additional metrics"""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > 5000:  # Log slow requests (>5 seconds)
        logger.warning(f"Slow request: {name} took {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    logger.info("Performance test started")
    logger.info(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    logger.info("Performance test completed")
    
    # Log summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Max response time: {stats.total.max_response_time}ms")


# Custom user classes for different scenarios
class AuthenticationLoadUser(HttpUser):
    """Focus on authentication endpoints"""
    wait_time = between(1, 2)
    
    @task
    def register_login_cycle(self):
        """Continuously register and login new users"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        email = f"auth_test_{random_suffix}@example.com"
        password = "AuthTest123!"
        
        # Register
        user_data = {
            "email": email,
            "password": password,
            "full_name": f"Auth Test {random_suffix}"
        }
        self.client.post("/auth/register", json=user_data)
        
        # Login
        login_data = {"username": email, "password": password}
        response = self.client.post("/auth/login", data=login_data)
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            # Test protected endpoint
            self.client.get("/auth/me", headers=headers)


class DatabaseStressUser(HttpUser):
    """Focus on database-intensive operations"""
    wait_time = between(0.5, 1.5)
    
    def on_start(self):
        """Setup user"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        self.email = f"db_stress_{random_suffix}@example.com"
        self.password = "DbStress123!"
        
        user_data = {
            "email": self.email,
            "password": self.password,
            "full_name": f"DB Stress {random_suffix}"
        }
        self.client.post("/auth/register", json=user_data)
        
        login_data = {"username": self.email, "password": self.password}
        response = self.client.post("/auth/login", data=login_data)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def create_and_submit_quiz(self):
        """Create quiz and immediately submit answers"""
        quiz_data = {
            "text": "Database stress test content with multiple concepts to generate questions.",
            "difficulty": random.choice(["easy", "medium", "hard"]),
            "num_questions": random.randint(5, 10)
        }
        
        # Create quiz
        response = self.client.post("/generate-quiz", json=quiz_data, headers=self.headers)
        if response.status_code == 200:
            quiz = response.json()
            quiz_id = quiz["id"]
            
            # Get quiz
            response = self.client.get(f"/quiz/{quiz_id}", headers=self.headers)
            if response.status_code == 200:
                quiz_data = response.json()
                questions = quiz_data.get("questions", [])
                
                # Submit answers
                answers = [random.randint(0, 3) for _ in questions]
                submission = {
                    "quiz_id": quiz_id,
                    "answers": answers
                }
                self.client.post("/submit-answers", json=submission, headers=self.headers)
    
    @task(1)
    def rapid_quiz_retrieval(self):
        """Rapidly retrieve quizzes to stress database reads"""
        # Try to get a quiz (might fail if none exist, that's ok)
        quiz_id = random.randint(1, 100)
        self.client.get(f"/quiz/{quiz_id}", headers=self.headers) 