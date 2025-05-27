import axios, { AxiosError } from 'axios';
import type { PreviousAnswer, RouteResponse } from '../types/APIResponses';

interface RandomRoutesResponse {
  routes: RouteResponse[];
}

interface RegistrationResponse {
  message: string;
  user_uuid: string;
}


interface PreviousAnswersResponse {
  previous_answers: PreviousAnswer[];
}

interface RoutePreferenceResponse {
  message?: string;
  error?: string;
}

/**
 * Fetches two random walking routes from the server
 * @returns Promise containing two random routes
 */
export const fetchRandomRoutes = async (): Promise<RandomRoutesResponse> => {
  try {
    const response = await axios.get<RandomRoutesResponse>(
      'http://localhost:8080/generate-routes/',
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] fetchRandomRoutes: Error fetching random routes:', error);
    throw error;
  }
};

export const checkLoginStatus = async (): Promise<boolean> => {
  try {
    const response = await axios.get('http://localhost:8080/check-login/', {
      withCredentials: true
    });
    return response.status === 200;
  } catch (error) {
    if (error instanceof AxiosError && error.response?.status === 401) {
      return false;
    }
    console.error('[api.ts] checkLoginStatus: Error checking login status:', error);
    return false;
  }
};

/**
 * Registers an anonymous user
 * @returns Promise containing registration data
 */
export const registerUser = async (): Promise<RegistrationResponse> => {
  try {
    const response = await axios.post<RegistrationResponse>(
      'http://localhost:8080/register/',
      {}, // Empty body for POST request
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] registerUser: Error registering user:', error);
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
      'http://localhost:8080/previous-answers/',
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
      'http://localhost:8080/prefer-route/',
      { selected_route_id, presented_routes_ids },
      { withCredentials: true }
    );
    return response.data;
  } catch (error) {
    console.error('[api.ts] saveRoutePreference: Error saving route preference:', error);
    throw error;
  }
};