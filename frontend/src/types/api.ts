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
