import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMyQuizzes, usePracticeStudyTopic } from "../hooks/useQuiz";
import Button from "../components/Button";
import type { QuizSummary, StudyTopicSummary } from "../types/api";

function formatDate(value?: string | null) {
  if (!value) return "Unknown date";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Unknown date";
  return parsed.toLocaleDateString();
}

function QuizRow({ quiz }: { quiz: QuizSummary }) {
  return (
    <li>
      <Link
        to={`/quiz/${quiz.id}`}
        className="block rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:border-indigo-400 dark:hover:border-indigo-500 transition-colors"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-semibold">{quiz.title}</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {quiz.topic || "No topic"} · {quiz.question_count} questions ·
              Created {formatDate(quiz.created_at)}
            </p>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
            {quiz.attempt_count > 0
              ? `Best score: ${quiz.best_score}`
              : "Not taken yet"}
          </p>
        </div>
      </Link>
    </li>
  );
}

function StudyTopicCard({
  topic,
  onPractice,
  isPracticing,
}: {
  topic: StudyTopicSummary;
  onPractice: (topic: StudyTopicSummary) => void;
  isPracticing: boolean;
}) {
  return (
    <li className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3 mb-4">
        <div>
          <h4 className="text-lg font-semibold">{topic.title}</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {topic.quiz_count} {topic.quiz_count === 1 ? "quiz" : "quizzes"} ·{" "}
            {topic.completed} completed
          </p>
        </div>
        {topic.can_practice && topic.id && (
          <Button
            variant="secondary"
            className="w-full md:w-auto"
            isLoading={isPracticing}
            onClick={() => onPractice(topic)}
          >
            New quiz on this topic
          </Button>
        )}
      </div>
      <ul className="space-y-3">
        {topic.quizzes.map((quiz) => (
          <QuizRow key={quiz.id} quiz={quiz} />
        ))}
      </ul>
    </li>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data, isLoading, error } = useMyQuizzes();
  const practiceMutation = usePracticeStudyTopic();

  const quizzes = data?.quizzes ?? [];
  const studyTopics = data?.study_topics ?? [];
  const totalQuizzes = data?.total_quizzes ?? 0;
  const completed = data?.completed ?? 0;
  const totalTopics = data?.total_topics ?? 0;

  const handlePractice = async (topic: StudyTopicSummary) => {
    if (!topic.id) return;
    try {
      const result = await practiceMutation.mutateAsync({
        study_topic_id: topic.id,
        num_questions: topic.quizzes[0]?.question_count || 5,
      });
      navigate(`/quiz/${result.id}`);
    } catch (practiceError) {
      console.error("Error generating a new quiz on this topic:", practiceError);
    }
  };

  return (
    <div className="space-y-8">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">Welcome, {user?.email}!</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Create a new quiz or keep practicing a topic you already started.
        </p>
        <Link to="/quiz/new">
          <Button className="w-full md:w-auto">Create New Quiz</Button>
        </Link>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold mb-4">Study Topics</h3>
        {isLoading && (
          <p className="text-gray-600 dark:text-gray-300">Loading your quizzes...</p>
        )}
        {error && (
          <p className="text-red-600 dark:text-red-400">
            Could not load your quizzes. Please try again.
          </p>
        )}
        {practiceMutation.isError && (
          <p className="mb-4 text-red-600 dark:text-red-400">
            Could not generate a new quiz on that topic. Please try again.
          </p>
        )}
        {!isLoading && !error && quizzes.length === 0 && (
          <p className="text-gray-600 dark:text-gray-300 italic">
            No quizzes created yet.
          </p>
        )}
        {!isLoading && studyTopics.length > 0 && (
          <ul className="space-y-4">
            {studyTopics.map((topic) => (
              <StudyTopicCard
                key={topic.id ?? `ungrouped-${topic.title}`}
                topic={topic}
                onPractice={handlePractice}
                isPracticing={
                  practiceMutation.isPending &&
                  practiceMutation.variables?.study_topic_id === topic.id
                }
              />
            ))}
          </ul>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Quick Stats</h3>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Topics</p>
              <p className="text-2xl font-bold">{totalTopics}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Total Quizzes</p>
              <p className="text-2xl font-bold">{totalQuizzes}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold">{completed}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <Link to="/quiz/new" className="block">
              <Button variant="secondary" className="w-full text-left">
                Create Quiz
              </Button>
            </Link>
            <Link to="/profile" className="block">
              <Button variant="secondary" className="w-full text-left">
                View Profile
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
