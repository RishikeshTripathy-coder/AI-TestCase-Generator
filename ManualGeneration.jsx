import { FormControl, Paper, TextField } from "@mui/material";
import { forwardRef, useState } from "react";
import { useErrors } from "../../hooks/useErrors";
import { isValidRequirement } from "../../utils/validRequirementsCheck";

const ManualGeneration = forwardRef((props, ref) => {
  console.count("ManualGeneration");
  const [inputRequirement, setInputRequirement] = useState("");
  const { errors, inputFocusHandler, inputBlurHandler } = useErrors();
  const inputRequirementFocusHandler = () => {
    if (errors?.input_requirement_error) {
      inputFocusHandler("input_requirement_error");
    }
  };
  const inputRequirementBlurHandler = (e) => {
    const inputValue = e.target.value;
    // Check if the manual input requirement meets the valid requirements
    const isValidRequirements = isValidRequirement(inputValue);
    if (!isValidRequirements.valid) {
      inputBlurHandler("input_requirement_error", isValidRequirements.message);
    } else {
      // Clear error if valid
      inputBlurHandler("input_requirement_error", "");
    }
  };
  return (
    <Paper variant="outlined" sx={{ p: 2, bgcolor: "white" }}>
      <FormControl fullWidth>
        <TextField
          multiline
          fullWidth
          size="small"
          required
          inputRef={ref}
          value={inputRequirement}
          onChange={(e) => setInputRequirement(e.target.value)}
          onFocus={inputRequirementFocusHandler}
          onBlur={inputRequirementBlurHandler}
          error={Boolean(errors?.input_requirement_error)}
          helperText={errors?.input_requirement_error}
          minRows={7}
          maxRows={12}
          margin="normal"
          label="Manual Requirements Input"
          variant="outlined"
          sx={{
            textarea: {
              resize: "vertical",
            },
          }}
        />
      </FormControl>
    </Paper>
  );
});

export default ManualGeneration;
