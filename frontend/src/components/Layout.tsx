import { Satellite, Orbit, ShieldAlert, LogOut } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-3 py-3 lg:h-16 lg:flex-nowrap lg:py-0">
            <div className="flex min-w-0 items-center gap-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <Satellite className="w-6 h-6 text-white" />
              </div>
              <div className="min-w-0">
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  Apex
                </h1>
                <p className="hidden text-xs text-slate-500 dark:text-slate-400 sm:block">
                  Constellation planning & synthetic risk replay
                </p>
              </div>
            </div>

            <nav
              aria-label="Primary"
              className="order-last grid w-full min-w-0 grid-cols-3 items-center gap-1 lg:order-none lg:ml-auto lg:flex lg:w-auto"
            >
              <NavLink
                to="/"
                className={({ isActive }) =>
                  `flex min-w-0 flex-col items-center justify-center gap-1 rounded-lg px-1 py-2 text-[11px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 sm:flex-row sm:gap-2 sm:px-3 sm:text-sm ${
                    isActive
                      ? "bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
                  }`
                }
              >
                <Satellite className="w-4 h-4 shrink-0" />
                Planning
              </NavLink>
              <NavLink
                to="/constellations"
                className={({ isActive }) =>
                  `flex min-w-0 flex-col items-center justify-center gap-1 rounded-lg px-1 py-2 text-[11px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 sm:flex-row sm:gap-2 sm:px-3 sm:text-sm ${
                    isActive
                      ? "bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
                  }`
                }
              >
                <Orbit className="w-4 h-4 shrink-0" />
                Constellations
              </NavLink>
              <NavLink
                to="/demo/replay"
                className={({ isActive }) =>
                  `flex min-w-0 flex-col items-center justify-center gap-1 rounded-lg px-1 py-2 text-[11px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2 sm:flex-row sm:gap-2 sm:px-3 sm:text-sm ${
                    isActive
                      ? "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-700"
                  }`
                }
              >
                <ShieldAlert className="w-4 h-4 shrink-0" />
                Risk replay
              </NavLink>
            </nav>

            <div className="ml-auto flex shrink-0 items-center gap-3 border-l border-slate-200 pl-3 dark:border-slate-700 lg:ml-0 lg:pl-4">
              <div className="hidden text-right sm:block">
                <p className="max-w-32 truncate text-sm font-medium text-slate-700 dark:text-slate-200">
                  {user?.name || user?.email}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 capitalize">
                  {user?.plan}
                </p>
              </div>
              <button
                type="button"
                onClick={logout}
                aria-label="Log out"
                className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
                title="Log out"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>
    </div>
  );
}
