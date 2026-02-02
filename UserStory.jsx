import {
  Button,
  Container,
  FormControl,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useErrors } from "../../hooks/useErrors";
import { useNavigate } from "react-router-dom";

const UserStory = ({ type, handleClose }) => {
  const navigate = useNavigate();
  const { errors, inputFocusHandler, inputBlurHandler } = useErrors();
  const summaryFocusHandler = () => {
    inputFocusHandler("summary_error");
  };
  const summaryBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 10) {
      inputBlurHandler(
        "summary_error",
        "Summary must be at least 10 characters long"
      );
    }
  };

  const descriptionFocusHandler = () => {
    inputFocusHandler("description_error");
  };
  const descriptionBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 10) {
      inputBlurHandler(
        "description_error",
        "Description must be at least 10 characters long"
      );
    }
  };
  const acceptanceCriteriaFocusHandler = () => {
    inputFocusHandler("ac_error");
  };
  const acceptanceCriteriaBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 10) {
      inputBlurHandler(
        "ac_error",
        "Acceptance Criteria must be at least 10 characters long"
      );
    }
  };

  const userStoryCancelHandler = () => {
    navigate("/");
  };

  return (
    <Container maxWidth="lg">
      <form>
        <Paper variant="outlined" sx={{ p: 2, bgcolor: "white" }}>
          <Typography variant="h6" textAlign={"center"} fontWeight={"bold"}>
            {type !== "edit" && "Create New User Story"}
          </Typography>
          <FormControl fullWidth>
            <TextField
              fullWidth
              error={Boolean(errors?.summary_error)}
              helperText={errors?.summary_error}
              size="small"
              onFocus={summaryFocusHandler}
              onBlur={summaryBlurHandler}
              label="Summary"
              margin="normal"
            />
          </FormControl>
          <FormControl fullWidth>
            <TextField
              fullWidth
              size="small"
              error={Boolean(errors?.description_error)}
              helperText={errors?.description_error}
              onFocus={descriptionFocusHandler}
              onBlur={descriptionBlurHandler}
              label="Description"
              margin="normal"
            />
          </FormControl>
          <FormControl fullWidth>
            <TextField
              multiline
              fullWidth
              size="small"
              error={Boolean(errors?.ac_error)}
              helperText={errors?.ac_error}
              onFocus={acceptanceCriteriaFocusHandler}
              onBlur={acceptanceCriteriaBlurHandler}
              minRows={7}
              maxRows={12}
              margin="normal"
              label="Acceptance Criteria"
              variant="outlined"
              sx={{
                textarea: {
                  resize: "vertical",
                },
              }}
            />
          </FormControl>
          <Button size="small" sx={{ mt: 2 }} variant="contained">
            {type === "edit" ? "Edit" : "Create"}
          </Button>

          {type === "edit" && (
            <Button
              size="small"
              onClick={handleClose}
              sx={{ mt: 2, ml: 1 }}
              variant="outlined"
            >
              Cancel
            </Button>
          )}
          {type !== "edit" && (
            <Button
              size="small"
              onClick={userStoryCancelHandler}
              sx={{ mt: 2, ml: 1 }}
              variant="outlined"
            >
              Cancel
            </Button>
          )}
        </Paper>
      </form>
    </Container>
  );
};

export default UserStory;
