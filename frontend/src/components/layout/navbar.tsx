'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { createClient } from '@/utils/supabase/client';
import {
  Brain,
  Trophy,
  FileText,
  List,
  X,
  SignOut,
  User,
} from '@phosphor-icons/react';

export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string; weight?: string; size?: number }>;
}

export const navItems: NavItem[] = [
  { label: 'JD Analysis', href: '/jd-analysis', icon: FileText },
  { label: 'Rank Candidates', href: '/rank', icon: Trophy },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [userEmail, setUserEmail] = React.useState<string | null>(null);
  const supabase = createClient();

  React.useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      if (data.user) setUserEmail(data.user.email || null);
    });
    const { data: authListener } = supabase.auth.onAuthStateChange((_, session) => {
      setUserEmail(session?.user?.email || null);
    });
    return () => authListener.subscription.unsubscribe();
  }, [supabase.auth]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push('/auth/login');
    router.refresh();
  };

  const userInitial = userEmail ? userEmail[0].toUpperCase() : '?';

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="flex h-14 items-center justify-between px-5 md:px-8 max-w-screen-2xl mx-auto">

          {/* Brand */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-foreground text-background">
              <Brain size={15} weight="bold" />
            </div>
            <span className="font-bold text-sm tracking-tight">TalentIntel</span>
          </Link>

          {/* Desktop Nav pill */}
          <nav className="hidden md:flex items-center bg-muted/60 border border-border/50 rounded-full px-1.5 py-1 gap-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-150 ${isActive
                    ? 'bg-background text-foreground shadow-sm border border-border/60'
                    : 'text-muted-foreground hover:text-foreground'
                    }`}
                >
                  <Icon size={13} weight={isActive ? 'bold' : 'regular'} />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right controls */}
          <div className="flex items-center gap-2">

            {/* Avatar dropdown */}
            <div className="relative group hidden md:block">
              <button className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-border/60 hover:bg-muted transition-colors cursor-pointer">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-foreground text-background text-[10px] font-bold shrink-0">
                  {userInitial}
                </span>
                <span className="text-xs text-muted-foreground max-w-[100px] truncate hidden lg:block">
                  {userEmail || 'Account'}
                </span>
              </button>
              <div className="absolute right-0 top-full mt-2 w-52 bg-popover border border-border rounded-xl shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-all duration-150 origin-top-right scale-95 group-hover:scale-100 z-50">
                <div className="p-3 border-b border-border/50">
                  <p className="text-xs font-semibold text-foreground truncate">{userEmail}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">Recruiter Portal</p>
                </div>
                <div className="p-1.5">
                  <button
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 px-3 py-2 rounded-lg text-sm text-destructive hover:bg-destructive/10 transition-colors cursor-pointer"
                  >
                    <SignOut size={14} weight="regular" />
                    Sign out
                  </button>
                </div>
              </div>
            </div>

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen(true)}
              className="md:hidden flex items-center justify-center h-8 w-8 rounded-lg border border-border/60 hover:bg-muted transition-colors cursor-pointer"
            >
              <List size={16} weight="regular" className="text-muted-foreground" />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-[60] flex">
          <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative ml-auto w-72 h-full bg-background border-l border-border flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between p-4 border-b border-border/50">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-md bg-foreground text-background">
                  <Brain size={13} weight="bold" />
                </div>
                <span className="font-bold text-sm">TalentIntel</span>
              </div>
              <button onClick={() => setMobileOpen(false)} className="p-1 rounded-lg hover:bg-muted cursor-pointer">
                <X size={16} weight="regular" className="text-muted-foreground" />
              </button>
            </div>
            <nav className="flex-1 p-4 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${isActive
                      ? 'bg-muted text-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                      }`}
                  >
                    <Icon size={15} weight={isActive ? 'bold' : 'regular'} />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            <div className="p-4 border-t border-border/50">
              <div className="flex items-center gap-3 mb-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-foreground text-background text-xs font-bold shrink-0">
                  {userInitial}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground truncate">{userEmail || 'Guest'}</p>
                  <p className="text-[10px] text-muted-foreground">Recruiter Portal</p>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 px-3 py-2 rounded-lg text-sm text-destructive hover:bg-destructive/10 transition-colors cursor-pointer"
              >
                <SignOut size={14} weight="regular" />
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
