import { useState } from 'react';
import { Upload, FileText, CheckCircle2, Loader2 } from 'lucide-react';
import { toast } from 'react-toastify';
import api from '../utils/axios';
import type { ImportResponse } from '../types';
import { Link } from 'react-router-dom';

const ImportForm = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResponse | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (validateFile(droppedFile)) {
      setFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };

  const validateFile = (file: File) => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (extension !== 'xlsx' && extension !== 'bc3') {
      toast.error('Solo se aceptan archivos .xlsx o .bc3');
      return false;
    }
    return true;
  };

  const handleImport = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post<ImportResponse>('/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
      toast.success('Presupuesto importado correctamente');
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Error al importar el archivo';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-10 text-center">
        <h2 className="text-3xl font-serif text-primary mb-2">Importar Presupuesto</h2>
        <p className="text-accent italic">Sube archivos Excel (.xlsx) o BC3 para la extracción automática de ratios.</p>
      </div>

      {!result ? (
        <div className="bg-white border border-border p-8 shadow-sm">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              relative border-2 border-dashed rounded-none p-12 text-center transition-all duration-300
              ${isDragging ? 'border-accent bg-secondary/50' : 'border-border bg-secondary/10 hover:bg-secondary/30'}
              ${file ? 'bg-white' : ''}
            `}
          >
            <input
              type="file"
              onChange={handleFileChange}
              accept=".xlsx,.bc3"
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            
            {!file ? (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <Upload className="w-12 h-12 text-accent/50" />
                </div>
                <div>
                  <p className="text-lg font-medium text-primary">Arrastra tu archivo aquí</p>
                  <p className="text-sm text-accent">o haz clic para seleccionar (Excel o BC3)</p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-center">
                  <FileText className="w-12 h-12 text-accent" />
                </div>
                <div>
                  <p className="text-lg font-medium text-primary">{file.name}</p>
                  <p className="text-sm text-accent">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                  className="text-xs text-error underline uppercase tracking-widest"
                >
                  Quitar archivo
                </button>
              </div>
            )}
          </div>

          <div className="mt-8 flex justify-end space-x-4">
            <button
              onClick={reset}
              className="px-6 py-2 text-sm uppercase tracking-widest text-accent hover:text-primary transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleImport}
              disabled={!file || loading}
              className={`
                px-8 py-2 bg-primary text-white text-sm uppercase tracking-widest transition-all
                disabled:opacity-50 disabled:cursor-not-allowed hover:bg-accent
                flex items-center
              `}
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Procesando...
                </>
              ) : (
                'Confirmar Importación'
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-border p-12 text-center animate-in zoom-in duration-500">
          <div className="flex justify-center mb-6">
            <CheckCircle2 className="w-16 h-16 text-success" />
          </div>
          <h3 className="text-2xl font-serif text-primary mb-4">¡Importación Exitosa!</h3>
          <p className="text-accent mb-8">
            El presupuesto ha sido procesado y los ratios extraídos correctamente.
          </p>
          
          <div className="bg-secondary/50 p-6 mb-10 text-left border-l-2 border-accent">
            <p className="text-xs text-accent uppercase tracking-widest mb-2 font-bold">Trazabilidad SHA-256</p>
            <code className="text-xs break-all text-primary block bg-white p-2 border border-border">
              {result.file_hash}
            </code>
          </div>

          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link
              to="/master"
              className="px-8 py-3 bg-primary text-white text-sm uppercase tracking-widest hover:bg-accent transition-all"
            >
              Ver Master de Ratios
            </Link>
            <button
              onClick={reset}
              className="px-8 py-3 border border-border text-sm uppercase tracking-widest hover:bg-secondary transition-all"
            >
              Importar otro
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImportForm;
