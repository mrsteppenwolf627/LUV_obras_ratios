import { Archive, Home, PieChart, Table, Upload } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: (string | undefined | null | boolean | { [key: string]: boolean })[]) {
  return twMerge(clsx(inputs));
}

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Home', path: '/', icon: Home },
    { name: 'Importar', path: '/import', icon: Upload },
    { name: 'Master', path: '/master', icon: Table },
    { name: 'Archivados', path: '/archived', icon: Archive },
    { name: 'Visuales', path: '/visuales', icon: PieChart },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-20 justify-between">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3">
              <img src="/logo.svg" alt="LUV" className="h-8 w-8" />
              <span className="font-serif text-2xl uppercase tracking-widest text-primary">LUV RATIOS</span>
            </Link>
          </div>

          <div className="hidden items-center sm:flex sm:space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;

              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={cn(
                    'inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium transition-colors',
                    isActive
                      ? 'border-accent text-primary'
                      : 'border-transparent text-accent hover:border-border hover:text-primary',
                  )}
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>

          <div className="flex items-center">
            <a
              href="https://luv.studio"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs uppercase tracking-widest text-accent transition-colors hover:text-primary"
            >
              luv.studio
            </a>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
