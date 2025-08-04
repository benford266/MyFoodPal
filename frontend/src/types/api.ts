// API Types and Interfaces

export interface User {
  id: number
  email: string
  name: string
  liked_foods: string
  disliked_foods: string
  must_use_ingredients: string
  created_at: string
  is_active: boolean
}

export interface LoginRequest {
  username: string // Email
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  name: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface RecipeIngredient {
  item: string
  quantity: string
  unit: string
}

export interface Recipe {
  name: string
  prep_time: string
  cook_time: string
  servings: number
  cuisine_inspiration: string
  difficulty: string
  ingredients: RecipeIngredient[]
  instructions: string[]
  image_path?: string
}

export interface ShoppingListItem {
  ingredient: string
  quantity: string
  unit: string
  used_in_recipes: string[]
}

export interface RecipeGenerationRequest {
  liked_foods: string[]
  disliked_foods: string[]
  must_use_ingredients: string[]
  recipe_count: number
  serving_size: number
  generate_images: boolean
}

export interface MealPlanResponse {
  id: number
  name: string
  serving_size: number
  recipe_count: number
  recipes: Recipe[]
  shopping_list: ShoppingListItem[]
  created_at: string
  rating?: number
  notes: string
}

export interface GenerationTaskResponse {
  id: number
  status: 'pending' | 'generating_recipes' | 'generating_images' | 'completed' | 'failed'
  progress: number
  current_step: string
  meal_plan_id?: number
  error_message: string
  created_at: string
}

export interface UserPreferencesUpdate {
  liked_foods?: string[]
  disliked_foods?: string[]
  must_use_ingredients?: string[]
}

export interface APIError {
  detail: string
}