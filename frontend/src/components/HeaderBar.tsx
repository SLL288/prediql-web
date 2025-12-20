'use client'

import clsx from 'clsx'
import { apiMode } from '../lib/apiClient'

export function HeaderBar() {
  return (
    <header className="mb-6 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 text-white">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-cyan-600 text-xl font-bold shadow-lg">
            P
          </div>
          <div>
            <h1 className="text-2xl font-semibold">PrediQL Web</h1>
            <p className="text-sm text-slate-300">GraphQL recon, simplified</p>
            <a
              href="https://arxiv.org/pdf/2510.10407"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-cyan-200 hover:text-white underline underline-offset-4"
            >
              Research paper (arXiv 2510.10407)
            </a>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className={clsx('rounded-full px-3 py-1 font-semibold text-slate-900', 'bg-amber-300')}>
            {apiMode === 'mock' ? 'Mock API' : 'REST API'}
          </span>
        </div>
      </div>
      <div className="rounded-2xl border border-amber-400/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-50">
        Only test endpoints you own or have permission to test.
      </div>
    </header>
  )
}
