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
        className="block min-h-11 rounded-xl border border-stone-200 dark:border-stone-700 p-4 hover:border-teal-700 dark:hover:border-teal-500 transition-colors"
      >
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="font-semibold">{quiz.title}</p>
            <p className="text-sm text-stone-600 dark:text-stone-400">
              {quiz.topic || "No topic"} · {quiz.question_count} questions ·
              Created {formatDate(quiz.created_at)}
            </p>
          </div>
          <p className="text-sm text-stone-500 dark:text-stone-400 sm:whitespace-nowrap">
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
    <li className="rounded-2xl border border-stone-200 dark:border-stone-700 p-4">
      <div className="flex flex-col gap-3 mb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h4 className="text-lg font-semibold">{topic.title}</h4>
          <p className="text-sm text-stone-600 dark:text-stone-400">
            {topic.quiz_count} {topic.quiz_count === 1 ? "quiz" : "quizzes"} ·{" "}
            {topic.completed} completed
          </p>
        </div>
        {topic.can_practice && topic.id && (
          <Button
            variant="secondary"
            className="w-full sm:w-auto"
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
    <div className="space-y-6 sm:space-y-8">
      <div className="card p-5 sm:p-6">
        <p className="page-kicker mb-2">Library</p>
        <h2 className="page-title mb-2 text-2xl sm:text-3xl">
          Welcome back
        </h2>
        <p className="text-stone-600 dark:text-stone-300 mb-6">
          Signed in as {user?.email}. Create a new quiz or keep practicing a
          topic you already started.
        </p>
        <Link to="/quiz/new" className="inline-block w-full sm:w-auto">
          <Button className="w-full sm:w-auto">Create New Quiz</Button>
        </Link>
      </div>

      <div className="card p-5 sm:p-6">
        <h3 className="font-display text-xl font-semibold mb-4">Study Topics</h3>
        {isLoading && (
          <p className="text-stone-600 dark:text-stone-300">Loading your quizzes...</p>
        )}
        {error && (
          <p className="text-red-700 dark:text-red-400">
            Could not load your quizzes. Please try again.
          </p>
        )}
        {practiceMutation.isError && (
          <p className="mb-4 text-red-700 dark:text-red-400">
            Could not generate a new quiz on that topic. Please try again.
          </p>
        )}
        {!isLoading && !error && quizzes.length === 0 && (
          <div className="rounded-xl border border-dashed border-stone-300 dark:border-stone-700 px-4 py-8 text-center">
            <p className="text-stone-600 dark:text-stone-300 italic">
              No quizzes created yet.
            </p>
            <Link to="/quiz/new" className="mt-4 inline-block">
              <Button variant="outline">Start with a document or notes</Button>
            </Link>
          </div>
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

      <div className="grid gap-4 sm:grid-cols-2 sm:gap-6">
        <div className="card p-5 sm:p-6">
          <h3 className="font-display text-xl font-semibold mb-4">Quick Stats</h3>
          <div className="grid grid-cols-3 gap-2 sm:gap-4">
            <div className="rounded-xl bg-stone-50 dark:bg-stone-800/60 p-3 text-center sm:text-left">
              <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400">
                Topics
              </p>
              <p className="font-display text-2xl font-semibold">{totalTopics}</p>
            </div>
            <div className="rounded-xl bg-stone-50 dark:bg-stone-800/60 p-3 text-center sm:text-left">
              <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400">
                Total Quizzes
              </p>
              <p className="font-display text-2xl font-semibold">{totalQuizzes}</p>
            </div>
            <div className="rounded-xl bg-stone-50 dark:bg-stone-800/60 p-3 text-center sm:text-left">
              <p className="text-xs sm:text-sm text-stone-500 dark:text-stone-400">
                Completed
              </p>
              <p className="font-display text-2xl font-semibold">{completed}</p>
            </div>
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <h3 className="font-display text-xl font-semibold mb-4">Quick Actions</h3>
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
