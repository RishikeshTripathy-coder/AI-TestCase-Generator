import {
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  OutlinedInput,
  TextField,
  Typography,
} from "@mui/material";
import VisibilityOutlinedIcon from "@mui/icons-material/VisibilityOutlined";
import VisibilityOffOutlinedIcon from "@mui/icons-material/VisibilityOffOutlined";
import { memo, useState } from "react";
import { useErrors } from "../../hooks/useErrors";

const MemoizedPasswordField = memo(() => {
  console.count("PasswordField");
  const [showPassword, setShowPassword] = useState(false);
  const { errors, inputBlurHandler, inputFocusHandler } = useErrors();
  const handleClickShowPassword = () => setShowPassword((show) => !show);

  const handleMouseDownPassword = (event) => {
    event.preventDefault();
  };

  const handleMouseUpPassword = (event) => {
    event.preventDefault();
  };

  const passwordFocusHandler = () => {
    if (errors.api_key_error) {
      inputFocusHandler("api_key_error");
    }
  };
  const passwordBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 10) {
      inputBlurHandler("api_key_error", "Invalid API key");
    }
  };

  return (
    <Grid size={{ xs: 12, sm: 6, md: 5 }}>
      <FormControl fullWidth>
        {/* <InputLabel htmlFor="outlined-adornment-password">Password</InputLabel> */}

        <TextField
          fullWidth
          required
          size="small"
          name="jira_api_key"
          label="Jira API Token"
          error={Boolean(errors?.api_key_error)}
          helperText={errors?.api_key_error}
          margin="normal"
          onFocus={passwordFocusHandler}
          onBlur={passwordBlurHandler}
          type={showPassword ? "text" : "password"}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  aria-label={
                    showPassword ? "hide the password" : "display the password"
                  }
                  onClick={handleClickShowPassword}
                  onMouseDown={handleMouseDownPassword}
                  onMouseUp={handleMouseUpPassword}
                  edge="end"
                >
                  {showPassword ? (
                    <VisibilityOffOutlinedIcon />
                  ) : (
                    <VisibilityOutlinedIcon />
                  )}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </FormControl>
    </Grid>
  );
});

export default MemoizedPasswordField;
