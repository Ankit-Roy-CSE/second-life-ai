"use client"

import React, { createContext, useContext, useEffect, useState } from "react"
import { UserResponse } from "../../types/api"
import { apiClient } from "./api-client"

interface AuthContextType {
  user: UserResponse | null
  token: string | null
  login: (token: string, user: UserResponse) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    // Restore session from localStorage if available
    const savedToken = localStorage.getItem("slm_token")
    const savedUser = localStorage.getItem("slm_user")
    if (savedToken && savedUser) {
      setToken(savedToken)
      setUser(JSON.parse(savedUser))
      apiClient.setToken(savedToken)
    }
  }, [])

  const login = (newToken: string, newUser: UserResponse) => {
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem("slm_token", newToken)
    localStorage.setItem("slm_user", JSON.stringify(newUser))
    apiClient.setToken(newToken)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem("slm_token")
    localStorage.removeItem("slm_user")
    apiClient.setToken(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
