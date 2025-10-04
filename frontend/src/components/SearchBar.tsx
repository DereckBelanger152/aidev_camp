import { useState } from 'react';
import { Search } from 'lucide-react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading?: boolean;
}

export const SearchBar = ({ onSearch, isLoading = false }: SearchBarProps) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="relative group">
        <div className="absolute inset-0 bg-gradient-to-r from-neon-purple via-neon-cyan to-neon-pink rounded-2xl opacity-75 blur-md group-hover:opacity-100 transition-opacity duration-300" />

        <div className="relative glass rounded-2xl p-1">
          <div className="flex items-center gap-2 bg-black/50 rounded-xl p-4">
            <Search className="text-neon-cyan" size={24} />

            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Entrez le titre exact de la chanson..."
              disabled={isLoading}
              className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-lg disabled:opacity-50"
            />

            <button
              type="submit"
              disabled={!query.trim() || isLoading}
              className="px-6 py-2 bg-gradient-to-r from-neon-purple to-neon-cyan rounded-lg font-semibold text-white disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-neon-cyan/50 transition-all duration-300"
            >
              {isLoading ? 'Recherche...' : 'Rechercher'}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
};
