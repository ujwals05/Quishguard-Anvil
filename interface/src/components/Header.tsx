import React from 'react';
import { Search, Bell, Command, Search as SearchIcon } from 'lucide-react';

const Header = ({ title }: { title: string }) => {
  return (
    <header className="h-16 bg-surface/50 backdrop-blur-md border-b border-outline-variant flex items-center justify-between px-8 fixed top-0 right-0 left-64 z-40">
      <div className="flex items-center gap-6">
        <h1 className="text-lg font-semibold text-on-surface">{title}</h1>
        <div className="hidden md:flex items-center bg-surface-container-low border border-outline-variant rounded-lg px-3 py-1.5 w-80 group focus-within:border-primary/50 transition-all">
          <SearchIcon className="w-4 h-4 text-on-surface-variant group-focus-within:text-primary" />
          <input
            type="text"
            placeholder="Search signals, threats, or assets..."
            className="bg-transparent border-none focus:ring-0 text-sm w-full px-3 text-on-surface placeholder:text-on-surface-variant/50"
          />
          <div className="flex items-center gap-1 bg-surface-container-highest px-1.5 py-0.5 rounded border border-outline-variant text-[10px] text-on-surface-variant font-mono">
            <Command className="w-2.5 h-2.5" />
            <span>K</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 text-on-surface-variant hover:bg-surface-container-high rounded-full relative transition-all">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-error rounded-full border-2 border-surface"></span>
        </button>
        <div className="h-8 w-[1px] bg-outline-variant/30"></div>
        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end hidden sm:flex">
            <span className="text-xs font-bold text-primary tracking-widest uppercase">System Status</span>
            <span className="text-[10px] text-green-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
              Operational
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
