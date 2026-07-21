import { ThemeToggle } from "@/components/ThemeToggle";

const NAV_ITEMS = [{ label: "Overview", href: "/dashboard" }];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-1">
      <aside className="hidden w-56 shrink-0 border-r border-black/10 px-4 py-6 dark:border-white/10 sm:block">
        <div className="mb-8 text-lg font-semibold">Contract Review</div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 text-sm font-medium text-foreground/80 hover:bg-black/5 dark:hover:bg-white/10"
            >
              {item.label}
            </a>
          ))}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-black/10 px-6 py-4 dark:border-white/10">
          <h1 className="text-base font-semibold">Dashboard</h1>
          <ThemeToggle />
        </header>

        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
