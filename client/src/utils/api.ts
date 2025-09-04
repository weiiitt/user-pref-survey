import axios, { AxiosError } from 'axios';
import type { PreviousAnswer, RouteResponse } from '../types/APIResponses';

export const API_URL = 'https://minnow-tolerant-usefully.ngrok-free.app';

// Ensure all requests include the ngrok bypass header and send cookies by default
axios.defaults.withCredentials = true;
axios.defaults.headers.common['ngrok-skip-browser-warning'] = 'true';

interface RandomRoutesResponse {
  routes: RouteResponse[];
}

interface RegistrationResponse {
  message: string;
  participant_id: string;
}

interface LoginResponse {
  message: string;
  participant_id: string;
}

interface LoginStatusResponse {
  message: string;
  participant_id?: string;
}

interface PreviousAnswersResponse {
  previous_answers: PreviousAnswer[];
}

interface RoutePreferenceResponse {
  message?: string;
  error?: string;
}

interface QuestionImagesResponse {
  image1: string;
  image2: string;
  test_type: string;
  condition: number;
  question_num: number;
  time_taken?: number[];
  current_progress?: number;
  error?: string;
  show_inter_round_survey?: boolean;
  pending_survey_test_type?: string;
  pending_survey_condition?: number;
}

interface SubmitChoiceResponse {
  message: string;
  completed: boolean;
  show_inter_round_survey?: boolean;
}

export interface InterRoundQuestion {
  id: string;
  type: 'scale' | 'text';
  label: string;
  hint?: string;
}

export interface InterRoundQuestionsResponse {
  questions: InterRoundQuestion[];
  scale: { minValue: number; maxValue: number; minLabel: string; maxLabel: string };
  test_type: string;
  condition_number: number;
  is_final_for_test_type: boolean;
}

/**
 * Fetches two random walking routes from the server
 * @returns Promise containing two random routes
 */
export const fetchRandomRoutes = async (): Promise<RandomRoutesResponse> => {
  try {
    const response = await axios.get<RandomRoutesResponse>(
      `${API_URL}/generate-routes/`,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] fetchRandomRoutes: Error fetching random routes:', error);
    throw error;
  }
};

export const checkLoginStatus = async (): Promise<{ isLoggedIn: boolean; participantId?: string }> => {
  try {
    const response = await axios.get<LoginStatusResponse>(`${API_URL}/check-login/`, {
      withCredentials: true
    });
    return { 
      isLoggedIn: response.status === 200, 
      participantId: response.data.participant_id 
    };
  } catch (error) {
    if (error instanceof AxiosError && error.response?.status === 401) {
      return { isLoggedIn: false };
    }
    console.error('[api.ts] checkLoginStatus: Error checking login status:', error);
    return { isLoggedIn: false };
  }
};

/**
 * Fetches a unique participant ID from the server
 * @returns Promise containing a unique 4-digit participant ID
 */
export const fetchUniqueParticipantId = async (): Promise<string> => {
  try {
    const response = await axios.get<{ participant_id: string }>(
      `${API_URL}/generate-participant-id/`,
      { withCredentials: true }
    );
    return response.data.participant_id;
  } catch (error) {
    console.error('[api.ts] fetchUniqueParticipantId: Error fetching unique participant ID:', error);
    throw error;
  }
};

/**
 * Registers an anonymous user with a participant ID
 * @param participantId - The 4-digit participant ID
 * @returns Promise containing registration data
 */
export const registerUser = async (participantId: string): Promise<RegistrationResponse> => {
  try {
    const response = await axios.post<RegistrationResponse>(
      `${API_URL}/register/`,
      { participant_id: participantId },
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] registerUser: Error registering user:', error);
    throw error;
  }
};

/**
 * Logs in an existing user with their participant ID
 * @param participantId - The 4-digit participant ID
 * @returns Promise containing login data  
 */
export const loginUser = async (participantId: string): Promise<LoginResponse> => {
  try {
    const response = await axios.post<LoginResponse>(
      `${API_URL}/login/`,
      { participant_id: participantId },
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] loginUser: Error logging in user:', error);
    throw error;
  }
};

/**
 * Logs out the current user
 * @returns Promise containing logout confirmation
 */
export const logoutUser = async (): Promise<{ message: string }> => {
  try {
    const response = await axios.post<{ message: string }>(
      `${API_URL}/logout/`,
      {},
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] logoutUser: Error logging out user:', error);
    throw error;
  }
};

/**
 * Fetches all previous answers for the logged-in user.
 * @returns Promise containing previous answers
 */
export const fetchPreviousAnswers = async (): Promise<PreviousAnswersResponse> => {
  try {
    const response = await axios.get<PreviousAnswersResponse>(
      `${API_URL}/previous-answers/`,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] fetchPreviousAnswers: Error fetching previous answers:', error);
    throw error;
  }
};

/**
 * Saves the user's preferred route
 * @param selected_route_id - The id of the selected route
 * @param presented_routes_ids - The ids of the presented routes
 * @returns Promise containing the saved preference
 */
export const saveRoutePreference = async (selected_route_id: number, presented_routes_ids: number[]): Promise<RoutePreferenceResponse> => {
  try {
    const response = await axios.post<RoutePreferenceResponse>(
      `${API_URL}/prefer-route/`,
      { selected_route_id, presented_routes_ids },
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] saveRoutePreference: Error saving route preference:', error);
    throw error;
  }
};

/**
 * Fetches question images for current user progress
 * @returns Promise containing image data and progress info
 */
export const fetchQuestionImages = async (): Promise<QuestionImagesResponse> => {
  try {
    const response = await axios.get<QuestionImagesResponse>(
      `${API_URL}/api/get-question-images`,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] fetchQuestionImages: Error fetching question images:', error);
    throw error;
  }
};

/**
 * Submits user's choice for current question
 * @param choice - 0 for first image, 1 for second image
 * @param response_time - response time in seconds
 * @returns Promise containing submission result
 */
export const submitChoice = async (choice: number, response_time: number): Promise<SubmitChoiceResponse> => {
  try {
    const response = await axios.post<SubmitChoiceResponse>(
      `${API_URL}/api/submit-choice`,
      { choice, response_time },
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] submitChoice: Error submitting choice:', error);
    throw error;
  }
};

/**
 * Fetch inter-round survey questions and scale meta
 */
export const fetchInterRoundQuestions = async (): Promise<InterRoundQuestionsResponse> => {
  try {
    const response = await axios.get<InterRoundQuestionsResponse>(
      `${API_URL}/api/get-inter-round-questions`,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] fetchInterRoundQuestions: Error fetching inter-round questions:', error);
    throw error;
  }
};

/**
 * Submits inter-round survey with responses
 * @param responses - Survey response data
 * @returns Promise containing submission result
 */
export const submitInterRoundSurvey = async (
  responses: Record<string, number | string>
): Promise<{ message: string; success: boolean; all_completed?: boolean }> => {
  try {
    const response = await axios.post<{ message: string; success: boolean; all_completed?: boolean }>(
      `${API_URL}/api/submit-inter-round-survey`,
      responses,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] submitInterRoundSurvey: Error submitting inter-round survey:', error);
    throw error;
  }
};

/**
 * Checks if the user has completed all conditions and surveys
 */
export const checkCompletion = async (): Promise<{ all_completed: boolean }> => {
  try {
    const response = await axios.get<{ all_completed: boolean }>(
      `${API_URL}/api/check-completion`,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] checkCompletion: Error checking completion status:', error);
    // Treat errors as not completed to avoid false positives
    return { all_completed: false };
  }
};

/**
 * Fetches survey configuration including dynamic question counts
 * @returns Promise containing survey config
 */
export const fetchSurveyConfig = async (): Promise<{
  total_questions: number;
  tabletop_questions: number;
  robot_nav_questions: number;
  structure: { tabletop: Record<number, number>; robot_nav: Record<number, number> };
}> => {
  try {
    const response = await axios.get(
      `${API_URL}/api/get-survey-config`,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] fetchSurveyConfig: Error fetching survey config:', error);
    throw error;
  }
};

/**
 * Checks if user has completed the pre-activity survey
 * @returns Promise containing completion status and user data
 */
export const checkPreActivitySurvey = async (): Promise<{ completed: boolean; age?: number; sex?: string }> => {
  try {
    const response = await axios.get<{ completed: boolean; age?: number; sex?: string }>(
      `${API_URL}/api/check-pre-activity-survey`,
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] checkPreActivitySurvey: Error checking pre-activity survey status:', error);
    throw error;
  }
};

/**
 * Submits pre-activity survey data (age and sex)
 * @param age - User's age (1-120)
 * @param sex - User's sex
 * @returns Promise containing submission result
 */
export const submitPreActivitySurvey = async (age: number, sex: string): Promise<{ message: string; success: boolean }> => {
  try {
    const response = await axios.post<{ message: string; success: boolean }>(
      `${API_URL}/api/submit-pre-activity-survey`,
      { age, sex },
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] submitPreActivitySurvey: Error submitting pre-activity survey:', error);
    throw error;
  }
};

/**
 * Generates a random 4-digit participant ID (0000-9999)
 * Note: This doesn't check for collisions - use fetchUniqueParticipantId() for collision-free IDs
 * @returns 4-digit string
 */
export const generateParticipantId = (): string => {
  return Math.floor(Math.random() * 10000).toString().padStart(4, '0');
};