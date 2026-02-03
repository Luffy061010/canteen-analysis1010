const TOKEN_KEY = 'token'
const USER_INFO_KEY = 'userInfo'
const USER_ID_KEY = 'userId'

export const getAuthToken = () => {
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || ''
}

export const setAuthToken = (token, remember = true) => {
  if (remember) {
    localStorage.setItem(TOKEN_KEY, token)
    sessionStorage.removeItem(TOKEN_KEY)
  } else {
    sessionStorage.setItem(TOKEN_KEY, token)
    localStorage.removeItem(TOKEN_KEY)
  }
}

export const clearAuthToken = () => {
  localStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(TOKEN_KEY)
}

export const getStoredUserInfo = () => {
  const raw = localStorage.getItem(USER_INFO_KEY) || sessionStorage.getItem(USER_INFO_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch (e) {
    return null
  }
}

export const setStoredUserInfo = (info, remember = true) => {
  const raw = JSON.stringify(info || null)
  if (remember) {
    localStorage.setItem(USER_INFO_KEY, raw)
    sessionStorage.removeItem(USER_INFO_KEY)
  } else {
    sessionStorage.setItem(USER_INFO_KEY, raw)
    localStorage.removeItem(USER_INFO_KEY)
  }
}

export const clearStoredUserInfo = () => {
  localStorage.removeItem(USER_INFO_KEY)
  sessionStorage.removeItem(USER_INFO_KEY)
}

export const getStoredUserId = () => {
  return localStorage.getItem(USER_ID_KEY) || sessionStorage.getItem(USER_ID_KEY) || ''
}

export const setStoredUserId = (userId, remember = true) => {
  if (remember) {
    localStorage.setItem(USER_ID_KEY, String(userId))
    sessionStorage.removeItem(USER_ID_KEY)
  } else {
    sessionStorage.setItem(USER_ID_KEY, String(userId))
    localStorage.removeItem(USER_ID_KEY)
  }
}

export const clearStoredUserId = () => {
  localStorage.removeItem(USER_ID_KEY)
  sessionStorage.removeItem(USER_ID_KEY)
}