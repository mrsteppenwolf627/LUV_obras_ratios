import { Link, useLocation } from 'react-router-dom';
import { Home, Upload, Table, Archive, PieChart } from 'lucide-react';
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
    { name: 'Visuales', path: '/ratios', icon: PieChart },
  ];

  return (
    <nav className="bg-white border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3">
              <img src="/logo.svg" alt="LUV" className="h-8 w-8" />
              <span className="text-2xl font-serif tracking-widest text-primary uppercase">LUV RATIOS</span>
            </Link>
          </div>
          
          <div className="hidden sm:flex sm:space-x-8 sm:items-center">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={cn(
                    "inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors border-b-2",
                    isActive 
                      ? "border-accent text-primary" 
                      : "border-transparent text-accent hover:text-primary hover:border-border"
                  )}
                >
                  <Icon className="w-4 h-4 mr-2" />
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
              className="text-xs text-accent hover:text-primary transition-colors tracking-widest uppercase"
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
