import { useState, useEffect } from 'react'

/**
 * Shared theme hook with localStorage persistence.
 * Toggles the `dark` class on document.documentElement.
 */
export function useTheme() {
    const [darkMode, setDarkMode] = useState(() => {
        const saved = localStorage.getItem('odaos-theme')
        if (saved) return saved === 'dark'
        return true // default dark
    })

    useEffect(() => {
        if (darkMode) {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
        localStorage.setItem('odaos-theme', darkMode ? 'dark' : 'light')
    }, [darkMode])

    return { darkMode, toggleTheme: () => setDarkMode((v) => !v) }
}
