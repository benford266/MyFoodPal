import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from 'react-query'
import toast from 'react-hot-toast'
import { recipesAPI } from '../services/api'
import { RecipeGenerationRequest, MealPlanResponse } from '../types/api'

interface RecipeGenerationFormProps {
  onMealPlanGenerated: (mealPlan: MealPlanResponse) => void
}

export const RecipeGenerationForm: React.FC<RecipeGenerationFormProps> = ({
  onMealPlanGenerated,
}) => {
  const [likedFoods, setLikedFoods] = useState<string[]>([])
  const [dislikedFoods, setDislikedFoods] = useState<string[]>([])
  const [mustUseIngredients, setMustUseIngredients] = useState<string[]>([])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{
    recipe_count: number
    serving_size: number
    generate_images: boolean
  }>({
    defaultValues: {
      recipe_count: 5,
      serving_size: 4,
      generate_images: true,
    },
  })

  const generateMutation = useMutation(recipesAPI.generateRecipesSync, {
    onSuccess: (data) => {
      onMealPlanGenerated(data)
      toast.success('Recipes generated successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Recipe generation failed')
    },
  })

  const onSubmit = (data: any) => {
    const request: RecipeGenerationRequest = {
      liked_foods: likedFoods,
      disliked_foods: dislikedFoods,
      must_use_ingredients: mustUseIngredients,
      recipe_count: data.recipe_count,
      serving_size: data.serving_size,
      generate_images: data.generate_images,
    }

    generateMutation.mutate(request)
  }

  const addItem = (items: string[], setItems: (items: string[]) => void, value: string) => {
    if (value.trim() && !items.includes(value.trim())) {
      setItems([...items, value.trim()])
    }
  }

  const removeItem = (items: string[], setItems: (items: string[]) => void, index: number) => {
    setItems(items.filter((_, i) => i !== index))
  }

  const TagInput: React.FC<{
    label: string
    items: string[]
    setItems: (items: string[]) => void
    placeholder: string
  }> = ({ label, items, setItems, placeholder }) => {
    const [inputValue, setInputValue] = useState('')

    const handleKeyPress = (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        addItem(items, setItems, inputValue)
        setInputValue('')
      }
    }

    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {label}
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {items.map((item, index) => (
            <span
              key={index}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-emerald-100 text-emerald-800"
            >
              {item}
              <button
                type="button"
                onClick={() => removeItem(items, setItems, index)}
                className="ml-2 text-emerald-600 hover:text-emerald-800"
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          className="input-field"
          placeholder={placeholder}
        />
        <p className="text-xs text-gray-500 mt-1">Press Enter to add items</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">Generate Your Meal Plan</h2>
      
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <TagInput
          label="Foods You Like"
          items={likedFoods}
          setItems={setLikedFoods}
          placeholder="e.g., chicken, pasta, vegetables"
        />

        <TagInput
          label="Foods to Avoid"
          items={dislikedFoods}
          setItems={setDislikedFoods}
          placeholder="e.g., mushrooms, shellfish, spicy food"
        />

        <TagInput
          label="Must-Use Ingredients"
          items={mustUseIngredients}
          setItems={setMustUseIngredients}
          placeholder="e.g., ingredients you need to use up"
        />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Recipes
            </label>
            <select {...register('recipe_count')} className="input-field">
              <option value={3}>3 recipes</option>
              <option value={5}>5 recipes</option>
              <option value={7}>7 recipes</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Serving Size
            </label>
            <select {...register('serving_size')} className="input-field">
              <option value={1}>1 person</option>
              <option value={2}>2 people</option>
              <option value={4}>4 people</option>
              <option value={6}>6 people</option>
              <option value={8}>8 people</option>
            </select>
          </div>
        </div>

        <div className="flex items-center">
          <input
            {...register('generate_images')}
            type="checkbox"
            className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
          />
          <label className="ml-2 block text-sm text-gray-900">
            Generate recipe images (takes longer)
          </label>
        </div>

        <button
          type="submit"
          disabled={generateMutation.isLoading}
          className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {generateMutation.isLoading ? (
            <span className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating Recipes...
            </span>
          ) : (
            '🍽️ Generate Recipes'
          )}
        </button>
      </form>
    </div>
  )
}