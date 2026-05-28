import { Archive, ArrowRight, PieChart, Table, Upload } from 'lucide-react';
import { Link } from 'react-router-dom';

const Home = () => {
  const cards = [
    {
      title: 'Importar Presupuesto',
      description: 'Sube archivos .xlsx o .bc3 para analizar nuevos ratios.',
      link: '/import',
      icon: Upload,
      accent: 'text-success',
    },
    {
      title: 'Ver Master',
      description: 'Explora la base de datos consolidada de ratios por capitulo.',
      link: '/master',
      icon: Table,
      accent: 'text-accent',
    },
    {
      title: 'Archivados',
      description: 'Consulta el historial de importaciones y trazabilidad.',
      link: '/archived',
      icon: Archive,
      accent: 'text-warning',
    },
    {
      title: 'Ratios Visuales',
      description: 'Analisis grafico de tendencias, rangos y comparativas de costes.',
      link: '/visuales',
      icon: PieChart,
      accent: 'text-primary',
    },
  ];

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-16 space-y-4 text-center">
        <h1 className="text-5xl font-serif tracking-tight text-primary">LUV Obras Ratios</h1>
        <p className="mx-auto max-w-2xl text-xl font-light text-accent">
          Analisis economico de presupuestos de obra.
          <br />
          <span className="italic">Luxury of precision</span> en cada detalle.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.title}
              to={card.link}
              className="group relative overflow-hidden border border-border bg-white p-10 transition-all duration-500 hover:border-accent"
            >
              <div className="relative z-10 flex h-full flex-col">
                <div
                  className={`mb-6 w-fit rounded-sm bg-secondary p-3 transition-colors duration-500 group-hover:bg-accent group-hover:text-white`}
                >
                  <Icon className="h-8 w-8" />
                </div>
                <h2 className="mb-3 font-serif text-2xl text-primary transition-transform duration-500 group-hover:translate-x-1">
                  {card.title}
                </h2>
                <p className="mb-8 flex-grow text-sm leading-relaxed text-accent">{card.description}</p>
                <div className="flex items-center text-xs font-medium uppercase tracking-widest text-primary transition-all group-hover:gap-2">
                  Explorar <ArrowRight className="ml-1 h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
                </div>
              </div>

              <div className="absolute right-0 top-0 -mr-12 -mt-12 h-24 w-24 rounded-full bg-secondary opacity-50 transition-transform duration-700 group-hover:scale-150" />
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default Home;
