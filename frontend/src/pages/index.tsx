import { useState } from 'react'
import Head from 'next/head'
import { RecipeGenerationForm } from '../components/RecipeGenerationForm'
import { MealPlanDisplay } from '../components/MealPlanDisplay'
import { AuthModal } from '../components/AuthModal'
import { useAuth } from '../hooks/useAuth'
import { MealPlanResponse } from '../types/api'

export default function Home() {
  const { user, logout } = useAuth()
  const [currentMealPlan, setCurrentMealPlan] = useState<MealPlanResponse | null>(null)
  const [showAuthModal, setShowAuthModal] = useState(false)

  const handleMealPlanGenerated = (mealPlan: MealPlanResponse) => {
    setCurrentMealPlan(mealPlan)
  }

  return (
    <>
      <Head>
        <title>FoodPal - AI Recipe Generator</title>
        <meta name="description" content="Generate personalized recipes and meal plans with AI" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-100">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-6">
              <div className="flex items-center">
                <h1 className="text-3xl font-bold text-emerald-600">🍽️ FoodPal</h1>
                <p className="ml-4 text-gray-600">AI-Powered Recipe Generator</p>
              </div>
              
              <div className="flex items-center space-x-4">
                {user ? (
                  <div className="flex items-center space-x-4">
                    <span className="text-gray-700">Welcome, {user.name}!</span>
                    <button
                      onClick={logout}
                      className="btn-secondary"
                    >
                      Logout
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowAuthModal(true)}
                    className="btn-primary"
                  >
                    Login / Register
                  </button>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {!user ? (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Welcome to FoodPal
              </h2>
              <p className="text-gray-600 mb-8">
                Please login or register to start generating personalized recipes
              </p>
              <button
                onClick={() => setShowAuthModal(true)}
                className="btn-primary text-lg px-8 py-3"
              >
                Get Started
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recipe Generation Form */}
              <div className="space-y-6">
                <RecipeGenerationForm onMealPlanGenerated={handleMealPlanGenerated} />
              </div>

              {/* Results Display */}
              <div className="space-y-6">
                {currentMealPlan ? (
                  <MealPlanDisplay mealPlan={currentMealPlan} />
                ) : (
                  <div className="card">
                    <div className="text-center py-8">
                      <div className="text-6xl mb-4">🍽️</div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Ready to Generate Recipes
                      </h3>
                      <p className="text-gray-600">
                        Fill out your preferences and click generate to start!
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>

        {/* Auth Modal */}
        {showAuthModal && (
          <AuthModal 
            isOpen={showAuthModal}
            onClose={() => setShowAuthModal(false)}
          />
        )}
      </div>
    </>
  )
}