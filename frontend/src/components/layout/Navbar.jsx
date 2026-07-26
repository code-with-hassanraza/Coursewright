import { useState, useRef, useEffect } from 'react'
import { NavLink, Link, useNavigate } from 'react-router-dom'
import useAuth from '../../hooks/useAuth'

const navLinkClass = ({ isActive }) =>
  `font-body-strong text-body-strong pb-1 border-b-2 transition-colors ${
    isActive ? 'text-primary border-primary' : 'text-ink border-transparent hover:text-primary'
  }`

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const menuRef = useRef(null)

  // Close the account dropdown on outside click.
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleLogout() {
    logout()
    setMenuOpen(false)
    setMobileOpen(false)
    navigate('/login')
  }

  return (
    <header className="nav-bar">
      {/* Left group: logo + primary nav links */}
      <div className="flex items-center gap-xl">
        <Link to="/" className="font-heading-lg text-heading-lg font-extrabold text-primary">
          Coursewright
        </Link>
        <nav className="hidden md:flex items-center gap-lg">
          <NavLink to="/fields" className={navLinkClass}>
            Discover
          </NavLink>
          {isAuthenticated && (
            <NavLink to="/profile" className={navLinkClass}>
              Dashboard
            </NavLink>
          )}
        </nav>
      </div>

      {/* Right group: either desktop actions or the mobile hamburger — always
          exactly one visible child here, keeping nav-bar's justify-between a
          clean 2-group split at every breakpoint. */}
      <div className="flex items-center gap-lg">
        <div className="hidden md:flex items-center gap-lg">
          {isAuthenticated ? (
            <>
              <Link to="/fields" className="btn-primary">
                Find Path
              </Link>
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  aria-label="Account menu"
                  aria-expanded={menuOpen}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-secondary-bg font-body-strong text-body-strong text-on-secondary"
                >
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                </button>
                {menuOpen && (
                  <div className="custom-shadow absolute right-0 top-12 w-48 rounded-md border border-hairline-soft bg-surface-elevated py-xs">
                    <Link
                      to="/profile"
                      onClick={() => setMenuOpen(false)}
                      className="block px-md py-sm font-body-sm text-body-sm text-ink hover:bg-surface-card"
                    >
                      Profile
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-md py-sm font-body-sm text-body-sm text-ink hover:bg-surface-card"
                    >
                      Log out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="font-body-strong text-body-strong text-ink hover:text-primary">
                Log in
              </Link>
              <Link to="/signup" className="btn-primary">
                Sign Up
              </Link>
            </>
          )}
        </div>

        <button
          onClick={() => setMobileOpen((v) => !v)}
          aria-label="Menu"
          aria-expanded={mobileOpen}
          className="md:hidden flex h-10 w-10 items-center justify-center"
        >
          <span className="material-symbols-outlined">{mobileOpen ? 'close' : 'menu'}</span>
        </button>
      </div>

      {/* Mobile panel — absolutely positioned so it doesn't disturb the
          2-group flex layout above. */}
      {mobileOpen && (
        <div className="absolute left-0 top-16 flex w-full flex-col gap-xs border-b border-hairline-soft bg-canvas p-margin md:hidden">
          <NavLink to="/fields" onClick={() => setMobileOpen(false)} className={navLinkClass}>
            Discover
          </NavLink>
          {isAuthenticated && (
            <NavLink to="/profile" onClick={() => setMobileOpen(false)} className={navLinkClass}>
              Dashboard
            </NavLink>
          )}
          <div className="my-xs border-t border-hairline-soft" />
          {isAuthenticated ? (
            <>
              <Link to="/fields" onClick={() => setMobileOpen(false)} className="btn-primary justify-center">
                Find Path
              </Link>
              <button onClick={handleLogout} className="btn-outline justify-center">
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" onClick={() => setMobileOpen(false)} className="btn-outline justify-center">
                Log in
              </Link>
              <Link to="/signup" onClick={() => setMobileOpen(false)} className="btn-primary justify-center">
                Sign Up
              </Link>
            </>
          )}
        </div>
      )}
    </header>
  )
}