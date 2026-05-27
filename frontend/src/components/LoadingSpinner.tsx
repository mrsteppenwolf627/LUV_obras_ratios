const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
    </div>
  );
};

export default LoadingSpinner;
