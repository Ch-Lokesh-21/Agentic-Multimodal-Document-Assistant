import React, { useState } from "react";
import { Button } from "../../../../app/components/ui/Button";

interface QueryInputProps {
  onSubmit: (query: string) => Promise<void>;
  isLoading: boolean;
}

export const QueryInput: React.FC<QueryInputProps> = ({
  onSubmit,
  isLoading,
}) => {
  const [query, setQuery] = useState("");

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!query.trim()) return;
    await onSubmit(query);
    setQuery("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 border-t border-gray-200 bg-white"
    >
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your documents..."
          disabled={isLoading}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <Button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white cursor-pointer"
        >
          {isLoading ? "Sending..." : "Send"}
        </Button>
      </div>
    </form>
  );
};
