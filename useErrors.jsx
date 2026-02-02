import { useState } from "react";

export const useErrors = () => {
  const [errors, setErrors] = useState({});

  const inputFocusHandler = (fieldName) => {
    setErrors((prev) => ({ ...prev, [`${fieldName}`]: "" }));
  };
  const inputBlurHandler = (fieldName, errorMsg) => {
    setErrors((prev) => ({ ...prev, [`${fieldName}`]: errorMsg }));
  };
  return {
    errors,
    setErrors,
    inputFocusHandler,
    inputBlurHandler,
  };
};
