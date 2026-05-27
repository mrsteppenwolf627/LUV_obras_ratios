import { Link } from 'react-router-dom';
import { Upload, Table, Archive, PieChart, ArrowRight } from 'lucide-react';

const Home = () => {
  const cards = [
    { 
      title: 'Importar Presupuesto', 
      description: 'Sube archivos .xlsx o .bc3 para analizar nuevos ratios.',
      link: '/import',
      icon: Upload,
      accent: 'text-success'
    },
    { 
      title: 'Ver Master', 
      description: 'Explora la base de datos consolidada de ratios por capítulo.',
      link: '/master',
      icon: Table,
      accent: 'text-accent'
    },
    { 
      title: 'Archivados', 
      description: 'Consulta el historial de importaciones y trazabilidad.',
      link: '/archived',
      icon: Archive,
      accent: 'text-warning'
    },
    { 
      title: 'Ratios Visuales', 
      description: 'Análisis gráfico de tendencias y distribución de costes.',
      link: '/ratios',
      icon: PieChart,
      accent: 'text-primary'
    },
  ];

  return (
    <div className="max-w-5xl mx-auto">
      <div className="text-center mb-16 space-y-4">
        <h1 className="text-5xl font-serif text-primary tracking-tight">LUV Obras Ratios</h1>
        <p className="text-xl text-accent font-light max-w-2xl mx-auto">
          Análisis económico de presupuestos de obra. <br />
          <span className="italic">Luxury of precision</span> en cada detalle.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.title}
              to={card.link}
              className="group p-10 bg-white border border-border hover:border-accent transition-all duration-500 relative overflow-hidden"
            >
              <div className="relative z-10 flex flex-col h-full">
                <div className={`mb-6 p-3 w-fit bg-secondary rounded-sm group-hover:bg-accent group-hover:text-white transition-colors duration-500`}>
                  <Icon className="w-8 h-8" />
                </div>
                <h2 className="text-2xl font-serif text-primary mb-3 group-hover:translate-x-1 transition-transform duration-500">
                  {card.title}
                </h2>
                <p className="text-accent text-sm leading-relaxed mb-8 flex-grow">
                  {card.description}
                </p>
                <div className="flex items-center text-xs tracking-widest uppercase font-medium text-primary group-hover:gap-2 transition-all">
                  Explorar <ArrowRight className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
              
              {/* Background accent decoration */}
              <div className="absolute top-0 right-0 w-24 h-24 bg-secondary -mr-12 -mt-12 rounded-full opacity-50 group-hover:scale-150 transition-transform duration-700"></div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default Home;
