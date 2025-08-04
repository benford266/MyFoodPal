import axios, { AxiosResponse } from 'axios'
import Cookies from 'js-cookie'
import {
  User,
  LoginRequest,
  RegisterRequest,
  Token,
  RecipeGenerationRequest,
  MealPlanResponse,
  GenerationTaskResponse,
  UserPreferencesUpdate,
  APIError
} from '../types/api'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = Cookies.get('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove('token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  async login(credentials: LoginRequest): Promise<Token> {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    const response = await api.post<Token>('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async register(userData: RegisterRequest): Promise<User> {
    const response = await api.post<User>('/api/auth/register', userData)
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/api/auth/me')
    return response.data
  },
}

// Users API
export const usersAPI = {
  async getProfile(): Promise<User> {
    const response = await api.get<User>('/api/users/profile')
    return response.data
  },

  async updatePreferences(preferences: UserPreferencesUpdate): Promise<User> {
    const response = await api.put<User>('/api/users/preferences', preferences)
    return response.data
  },
}

// Recipes API
export const recipesAPI = {
  async generateRecipes(request: RecipeGenerationRequest): Promise<GenerationTaskResponse> {
    const response = await api.post<GenerationTaskResponse>('/api/recipes/generate', request)
    return response.data
  },

  async generateRecipesSync(request: RecipeGenerationRequest): Promise<MealPlanResponse> {
    const response = await api.post<MealPlanResponse>('/api/recipes/generate-sync', request)
    return response.data
  },

  async getGenerationStatus(taskId: number): Promise<GenerationTaskResponse> {
    const response = await api.get<GenerationTaskResponse>(`/api/recipes/generate/${taskId}/status`)
    return response.data
  },

  async getMealPlans(): Promise<MealPlanResponse[]> {
    const response = await api.get<MealPlanResponse[]>('/api/recipes/')
    return response.data
  },

  async getMealPlan(id: number): Promise<MealPlanResponse> {
    const response = await api.get<MealPlanResponse>(`/api/recipes/${id}`)
    return response.data
  },
}

// Meal Plans API
export const mealPlansAPI = {
  async exportPDF(mealPlanId: number): Promise<Blob> {
    const response = await api.post(`/api/meal-plans/${mealPlanId}/export-pdf`, {}, {
      responseType: 'blob',
    })
    return response.data
  },

  async exportCustomPDF(data: {
    recipes: any[]
    shopping_list: any[]
    liked_foods: string[]
    disliked_foods: string[]
    serving_size: number
  }): Promise<Blob> {
    const response = await api.post('/api/meal-plans/export-pdf', data, {
      responseType: 'blob',
    })
    return response.data
  },
}

export default api