// Quiz question types
export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correct_answer: number;
}

// Quiz response from API
export interface QuizResponse {
  id: string;
  title: string;
  topic?: string;
  study_topic_id?: number | null;
  questions: QuizQuestion[];
  created_at?: string;
}

// Quiz answer submission
export interface AnswerSubmission {
  quiz_id: number;
  answers: number[]; // Array of selected answer indices
}

// Quiz result response
export interface QuizResult {
  quiz_id: number;
  score: number;
  total: number;
  answers: number[];
  correct_answers: number[];
}

// Upload document form data
export interface UploadDocumentForm {
  file: File;
  topic?: string;
  num_questions?: number;
}

// Quiz text generation form data
export interface GenerateQuizForm {
  content: string;
  topic?: string;
  num_questions?: number;
}

export interface GenerateQuizFromUrlForm {
  url: string;
  topic?: string;
  num_questions?: number;
}

export interface QuizSummary {
  id: number;
  title: string;
  topic?: string | null;
  created_at?: string | null;
  question_count: number;
  attempt_count: number;
  best_score: number | null;
  study_topic_id?: number | null;
}

export interface StudyTopicSummary {
  id: number | null;
  title: string;
  topic?: string | null;
  source_url?: string | null;
  can_practice: boolean;
  quiz_count: number;
  completed: number;
  quizzes: QuizSummary[];
}

export interface QuizListResponse {
  quizzes: QuizSummary[];
  study_topics: StudyTopicSummary[];
  total_quizzes: number;
  completed: number;
  total_topics: number;
}

export interface PracticeStudyTopicForm {
  study_topic_id: number;
  num_questions?: number;
}
