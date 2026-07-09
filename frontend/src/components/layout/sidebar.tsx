'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Cpu } from 'lucide-react';
import { navItems } from './navbar';

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex flex-col w-60 border-r border-border/40 bg-card/30 backdrop-blur-xs min-h-[calc(100vh-4rem)] sticky top-16 z-30 shrink-0">
      <div className="flex-1 flex flex-col justify-between p-4">
        <div className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer ${
                  isActive
                    ? 'bg-muted text-foreground font-semibold shadow-xs'
                    : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
                }`}
              >
                <Icon className={`h-4.5 w-4.5 transition-colors ${isActive ? 'text-primary' : ''}`} />
                {item.label}
              </Link>
            );
          })}
        </div>

        {/* AI status widget */}
        <div className="rounded-xl border border-border/40 bg-muted/20 p-3 flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Cpu className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs font-semibold text-foreground truncate">AI Engine Status</p>
              <p className="text-[10px] text-muted-foreground">🟢 Online & Active</p>
            </div>
          </div>
          <div className="w-full bg-border/40 h-1.5 rounded-full overflow-hidden mt-1">
            <div className="bg-primary h-full w-[85%] rounded-full" />
          </div>
          <span className="text-[9px] text-muted-foreground text-right block">85% API quota remaining</span>
        </div>
      </div>
    </aside>
  );
}
