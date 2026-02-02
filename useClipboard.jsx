import { useState, useCallback } from "react";

const useClipboard = () => {
  const [isCopied, setIsCopied] = useState(false);
  const [error, setError] = useState(null);

  const copyToClipboard = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setIsCopied(true);
      setError(null);
      // Reset copied state after 3 seconds
      setTimeout(() => setIsCopied(false), 3000);
    } catch (err) {
      console.log("Clipboard copy failed:", err);
      setError("Failed to copy to clipboard");
      setIsCopied(false);
    }
  }, []);

  return { isCopied, error, copyToClipboard };
};

export default useClipboard;
