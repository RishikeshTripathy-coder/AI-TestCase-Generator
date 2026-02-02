import { useState } from "react";

export const useAlert = () => {
  const [open, setOpen] = useState(false);
  return {
    open,
    setOpen,
  };
};
