import { useState } from 'react'
import { useMutation } from 'react-query'
import toast from 'react-hot-toast'
import { mealPlansAPI } from '../services/api'
import { MealPlanResponse, Recipe } from '../types/api'

interface MealPlanDisplayProps {
  mealPlan: MealPlanResponse
}

export const MealPlanDisplay: React.FC<MealPlanDisplayProps> = ({ mealPlan }) => {
  const [activeTab, setActiveTab] = useState<'recipes' | 'shopping'>('recipes')

  const exportPDFMutation = useMutation(mealPlansAPI.exportCustomPDF, {
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `FoodPal_Meal_Plan_${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('PDF exported successfully!')
    },
    onError: () => {
      toast.error('Failed to export PDF')
    },
  })

  const handleExportPDF = () => {
    exportPDFMutation.mutate({
      recipes: mealPlan.recipes,
      shopping_list: mealPlan.shopping_list,
      liked_foods: [],
      disliked_foods: [],
      serving_size: mealPlan.serving_size,
    })
  }

  const RecipeCard: React.FC<{ recipe: Recipe; index: number }> = ({ recipe, index }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {recipe.image_path && (
        <img
          src={recipe.image_path}
          alt={recipe.name}
          className="w-full h-48 object-cover"
        />
      )}
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {index + 1}. {recipe.name}
        </h3>
        
        <div className="flex flex-wrap gap-4 text-sm text-gray-600 mb-4">
          <span>⏱️ Prep: {recipe.prep_time}</span>
          <span>🍳 Cook: {recipe.cook_time}</span>
          <span>👥 Serves: {recipe.servings}</span>
          <span>📍 {recipe.cuisine_inspiration}</span>
          <span>📊 {recipe.difficulty}</span>
        </div>

        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">Ingredients:</h4>
          <ul className="space-y-1">
            {recipe.ingredients.map((ingredient, idx) => (
              <li key={idx} className="text-sm text-gray-700">
                • {ingredient.quantity} {ingredient.unit} {ingredient.item}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-2">Instructions:</h4>
          <ol className="space-y-2">
            {recipe.instructions.map((instruction, idx) => (
              <li key={idx} className="text-sm text-gray-700">
                <span className="font-medium text-emerald-600">{idx + 1}.</span> {instruction}
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{mealPlan.name}</h2>
            <p className="text-gray-600">
              {mealPlan.recipe_count} recipes for {mealPlan.serving_size} people
            </p>
          </div>
          <button
            onClick={handleExportPDF}
            disabled={exportPDFMutation.isLoading}
            className="btn-primary disabled:opacity-50"
          >
            {exportPDFMutation.isLoading ? 'Exporting...' : '📄 Export PDF'}
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('recipes')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'recipes'
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📖 Recipes ({mealPlan.recipes.length})
            </button>
            <button
              onClick={() => setActiveTab('shopping')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'shopping'
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🛒 Shopping List ({mealPlan.shopping_list.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'recipes' ? (
        <div className="space-y-6">
          {mealPlan.recipes.map((recipe, index) => (
            <RecipeCard key={index} recipe={recipe} index={index} />
          ))}
        </div>
      ) : (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Shopping List</h3>
          <div className="grid gap-3">
            {mealPlan.shopping_list.map((item, index) => (
              <div
                key={index}
                className="flex justify-between items-center py-2 px-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <span className="font-medium text-gray-900">
                    {item.quantity} {item.unit} {item.ingredient}
                  </span>
                  {item.used_in_recipes && item.used_in_recipes.length > 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      Used in: {item.used_in_recipes.join(', ')}
                    </div>
                  )}
                </div>
                <input
                  type="checkbox"
                  className="h-4 w-4 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}