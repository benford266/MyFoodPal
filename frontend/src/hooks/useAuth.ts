import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import Cookies from 'js-cookie'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'
import { User, LoginRequest, RegisterRequest } from '../types/api'

export const useAuth = () => {
  const queryClient = useQueryClient()
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Check if user is authenticated on mount
  useEffect(() => {
    const token = Cookies.get('token')
    setIsAuthenticated(!!token)
  }, [])

  // Get current user query
  const { data: user, isLoading } = useQuery<User>(
    'currentUser',
    authAPI.getCurrentUser,
    {
      enabled: isAuthenticated,
      retry: false,
      onError: () => {
        setIsAuthenticated(false)
        Cookies.remove('token')
      },
    }
  )

  // Login mutation
  const loginMutation = useMutation(authAPI.login, {
    onSuccess: (data) => {
      Cookies.set('token', data.access_token, { expires: 7 }) // 7 days
      setIsAuthenticated(true)
      queryClient.invalidateQueries('currentUser')
      toast.success('Logged in successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Login failed')
    },
  })

  // Register mutation
  const registerMutation = useMutation(authAPI.register, {
    onSuccess: () => {
      toast.success('Registration successful! Please log in.')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Registration failed')
    },
  })

  // Logout function
  const logout = () => {
    Cookies.remove('token')
    setIsAuthenticated(false)
    queryClient.clear()
    toast.success('Logged out successfully')
  }

  return {
    user,
    isAuthenticated,
    isLoading,
    login: loginMutation.mutate,
    register: registerMutation.mutate,
    logout,
    isLoginLoading: loginMutation.isLoading,
    isRegisterLoading: registerMutation.isLoading,
  }
}