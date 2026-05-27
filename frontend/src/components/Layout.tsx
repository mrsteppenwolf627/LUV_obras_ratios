import React from 'react';
import Navigation from './Navigation';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-secondary selection:bg-accent/20">
      <Navigation />
      
      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 w-full">
        <div className="animate-in fade-in duration-700">
          {children}
        </div>
      </main>

      <footer className="bg-white border-t border-border py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <div className="text-sm text-accent">
            © {new Date().getFullYear()} LUV Studio. Precision in every detail.
          </div>
          <div className="flex space-x-6">
            <a 
              href="https://luv.studio" 
              className="text-xs text-accent hover:text-primary transition-colors tracking-widest uppercase"
            >
              Website
            </a>
            <span className="text-border">|</span>
            <span className="text-xs text-accent tracking-widest uppercase">
              Ratios Platform v1.0
            </span>
          </div>
        </div>
      </footer>

      <ToastContainer 
        position="top-right"
        autoClose={3000}
        hideProgressBar
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
        toastClassName={() => "bg-white border border-border shadow-lg rounded-none p-4 flex items-center mb-2"}
        className="text-sm font-medium text-primary"
      />
    </div>
  );
};

export default Layout;
