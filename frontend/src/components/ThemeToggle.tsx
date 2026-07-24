"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // eslint-disable-next-line react-hooks/set-state-in-effect -- standard mount-detection pattern for next-themes
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <div className="h-9 w-16" />;
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="h-9 rounded-md border border-black/10 px-3 text-sm font-medium text-foreground transition-colors hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
      aria-label="Toggle color theme"
    >
      {isDark ? "Light mode" : "Dark mode"}
    </button>
  );
}
