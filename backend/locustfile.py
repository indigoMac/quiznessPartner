import random

from locust import HttpUser, between, task


class QuiznessUser(HttpUser):
    """Locust user simulation for the Quizness API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Set up user session - this runs once per user."""
        self.quiz_ids = []
        self.token = None

        # Some users will authenticate, others will be anonymous
        if random.choice([True, False]):
            self.authenticate()

    def authenticate(self):
        """Authenticate user and get token."""
        # Register a new user (or try to login if already exists)
        email = f"loadtest{random.randint(1, 10000)}@example.com"

        # Try to register
        response = self.client.post(
            "/api/v1/auth/register", json={"email": email, "password": "testpassword"}
        )

        # Login to get token
        response = self.client.post(
            "/api/v1/auth/token", data={"username": email, "password": "testpassword"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]

    def get_auth_headers(self):
        """Get authentication headers if user is authenticated."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(10)
    def health_check(self):
        """Frequently check health endpoint (most common request)."""
        self.client.get("/health")

    @task(5)
    def generate_quiz(self):
        """Generate a quiz from text content."""
        topics = ["Science", "History", "Geography", "Literature", "Math"]
        contents = [
            "The theory of relativity was developed by Einstein.",
            "World War II ended in 1945.",
            "The Amazon rainforest is located in South America.",
            "Shakespeare wrote many famous plays.",
            "Calculus is a branch of mathematics.",
        ]

        payload = {
            "content": random.choice(contents),
            "topic": random.choice(topics),
            "num_questions": random.randint(3, 10),
        }

        response = self.client.post(
            "/api/v1/generate-quiz", json=payload, headers=self.get_auth_headers()
        )

        if response.status_code == 200:
            quiz_id = response.json()["id"]
            self.quiz_ids.append(quiz_id)

    @task(3)
    def get_quiz(self):
        """Retrieve a quiz that was previously created."""
        if self.quiz_ids:
            quiz_id = random.choice(self.quiz_ids)
            self.client.get(f"/api/v1/quiz/{quiz_id}")
        else:
            # If no quizzes available, try to get a random quiz ID
            quiz_id = random.randint(1, 100)
            with self.client.get(
                f"/api/v1/quiz/{quiz_id}", catch_response=True
            ) as response:
                if response.status_code == 404:
                    response.success()  # 404 is expected for non-existent quizzes

    @task(2)
    def submit_quiz_answer(self):
        """Submit answers for a quiz."""
        if self.quiz_ids:
            quiz_id = random.choice(self.quiz_ids)

            # First get the quiz to know how many questions it has
            quiz_response = self.client.get(f"/api/v1/quiz/{quiz_id}")
            if quiz_response.status_code == 200:
                quiz_data = quiz_response.json()
                num_questions = len(quiz_data["questions"])

                # Generate random answers
                answers = [random.randint(0, 3) for _ in range(num_questions)]

                self.client.post(
                    "/api/v1/submit-answer",
                    json={"quiz_id": int(quiz_id), "answers": answers},
                )

    @task(1)
    def upload_document(self):
        """Upload a document to generate a quiz (simulated PDF)."""
        # Simulate a small PDF file
        pdf_content = b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"

        files = {"file": ("test.pdf", pdf_content, "application/pdf")}
        data = {
            "topic": random.choice(["Science", "History", "Math"]),
            "num_questions": str(random.randint(3, 8)),
        }

        response = self.client.post(
            "/api/v1/upload-document",
            files=files,
            data=data,
            headers=self.get_auth_headers(),
        )

        if response.status_code == 200:
            quiz_id = response.json()["id"]
            self.quiz_ids.append(quiz_id)


class AdminUser(HttpUser):
    """Simulates admin/power users who make more intensive requests."""

    wait_time = between(2, 5)
    weight = 1  # Only 10% of users will be admin users

    def on_start(self):
        self.quiz_ids = []
        self.authenticate()

    def authenticate(self):
        """Admin users always authenticate."""
        email = f"admin{random.randint(1, 100)}@example.com"

        response = self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "adminpassword"}
        )

        response = self.client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": "adminpassword"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(3)
    def create_large_quiz(self):
        """Create larger quizzes with more questions."""
        payload = {
            "content": (
                "This is comprehensive study material covering "
                "multiple topics " * 10
            ),
            "topic": "Comprehensive Study",
            "num_questions": random.randint(15, 25),
        }

        response = self.client.post(
            "/api/v1/generate-quiz",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}"},
        )

        if response.status_code == 200:
            quiz_id = response.json()["id"]
            self.quiz_ids.append(quiz_id)

    @task(2)
    def batch_quiz_retrieval(self):
        """Retrieve multiple quizzes in sequence."""
        for _ in range(random.randint(3, 7)):
            if self.quiz_ids:
                quiz_id = random.choice(self.quiz_ids)
                self.client.get(f"/api/v1/quiz/{quiz_id}")

    @task(1)
    def health_check(self):
        self.client.get("/health")
