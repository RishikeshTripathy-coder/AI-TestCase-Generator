import {
  Box,
  Typography,
  Select,
  MenuItem,
  TextField,
  Paper,
  OutlinedInput,
  Button,
  FormControl,
} from "@mui/material";
import EditUserStory from "./modal/EditUserStory";
import { useStoriesContext } from "../hooks/useStoriesContext";
import { memo, useState } from "react";
import { useErrors } from "../hooks/useErrors";

// RequirementDetails HOC
const withRequirementDetails = (Component) => {
  const MemoizedComponent = memo(Component);
  return (props) => {
    const {
      userStories,
      setSelectedStory: setUserSelectedStory,
      isTestScriptGenerating,
    } = useStoriesContext();
    return (
      <MemoizedComponent
        {...props}
        userStories={userStories}
        setUserSelectedStory={setUserSelectedStory}
        isTestScriptGenerating={isTestScriptGenerating}
      />
    );
  };
};

function RequirementDetails({
  userStories,
  setUserSelectedStory,
  isTestScriptGenerating,
}) {
  console.count("RequirementDetails");

  const menuItems = userStories?.map((story) => {
    return story.key;
  });

  const [selectedStory, setSelectedStory] = useState({
    key: "Select User Story",
  });

  // local editable copy of the fields so we can toggle readOnly
  const [localFields, setLocalFields] = useState({
    summary: "",
    description: "",
    acceptance_criteria: "",
  });

  const [isEditing, setIsEditing] = useState(false);

  // sync selectedStory into localFields when selection changes
  // (derived state kept simple here)
  const syncLocalFields = (story) => {
    setLocalFields({
      summary: story?.summary || "",
      description: story?.description || "",
      acceptance_criteria: story?.acceptance_criteria || "",
    });
  };

  // Handling errors:
  const { errors, inputFocusHandler, inputBlurHandler } = useErrors();

  // Functions to check the Summary Input field's focus and blur events
  const summaryFocusHandler = () => {
    if (errors.summary_error) {
      inputFocusHandler("summary_error");
    }
  };
  const summaryBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 25) {
      inputBlurHandler(
        "summary_error",
        "Summary should be at least 25 characters"
      );
    }
  };

  const descriptionFocusHandler = () => {
    if (errors.description_error) {
      inputFocusHandler("description_error");
    }
  };
  const descriptionBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 25) {
      inputBlurHandler(
        "description_error",
        "Description should be at least 25 characters"
      );
    }
  };

  const acceptanceCriteriaFocusHandler = () => {
    if (errors.ac_error) {
      inputFocusHandler("ac_error");
    }
  };
  const acceptanceCriteriaBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 120) {
      inputBlurHandler(
        "ac_error",
        "Acceptance Criteria should be at least 120 characters"
      );
    }
  };

  const userStoryChangeHandler = (e) => {
    const { value } = e.target;
    const foundUserStory = userStories.find((story) => story.key === value);
    console.log(foundUserStory);
    if (foundUserStory) {
      setSelectedStory(foundUserStory);
      setUserSelectedStory(foundUserStory);
      syncLocalFields(foundUserStory);
    }
  };

  const handleFieldChange = (field) => (e) => {
    setLocalFields((prev) => ({ ...prev, [field]: e.target.value }));
  };

  const handleToggleEdit = () => {
    // If cancelling edit, reset local fields to selectedStory values
    if (isEditing) {
      syncLocalFields(selectedStory);
      // Also clear any existing errors
      Object.keys(errors).forEach((key) => {
        inputBlurHandler(key, "");
      });
    }
    setIsEditing((v) => !v);
  };

  const userStorySaveHandler = () => {
    // basic validation

    // update the selected story with the local fields
    const updatedStory = {
      ...selectedStory,
      summary: localFields.summary,
      description: localFields.description,
      acceptance_criteria: localFields.acceptance_criteria,
    };
    console.log("Updated Story:", updatedStory);
    setSelectedStory(updatedStory);
    setUserSelectedStory(updatedStory);
    setIsEditing(false);
    alert("User Story Updated Successfully!");
  };

  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: "white" }}>
      <Box
        component={"div"}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 1,
        }}
      >
        <Typography
          variant="h6"
          component={"span"}
          fontWeight={"bold"}
          gutterBottom
        >
          Select Requirement
        </Typography>
        <Box component={"div"} sx={{ display: "flex", alignItems: "center" }}>
          <Button
            variant={isEditing ? "outlined" : "contained"}
            size="small"
            onClick={handleToggleEdit}
            disabled={
              selectedStory.key === "Select User Story" ||
              isTestScriptGenerating
            }
          >
            {isEditing ? "Cancel" : "Edit"}
          </Button>
          {isEditing && (
            <Button
              variant="contained"
              onClick={userStorySaveHandler}
              size="small"
              sx={{ ml: "7px" }}
              disabled={Boolean(
                errors.summary_error ||
                  errors.description_error ||
                  errors.ac_error
              )}
            >
              Save
            </Button>
          )}
        </Box>
      </Box>
      <Select
        fullWidth
        size="small"
        value={selectedStory.key}
        onChange={userStoryChangeHandler}
        sx={{ mb: 1 }}
      >
        <MenuItem value="Select User Story">Select User Story</MenuItem>
        {menuItems?.map((item) => {
          return (
            <MenuItem key={item} value={item}>
              {item}
            </MenuItem>
          );
        })}
      </Select>
      {/* <FormControl fullWidth variant="outlined" margin="normal">
        <TextField
          size="small"
          fullWidth
          name="summary"
          label={isEditing ? "Summary" : ""}
          onFocus={summaryFocusHandler}
          onBlur={summaryBlurHandler}
          error={Boolean(errors?.summary_error)}
          sx={{ mb: errors?.summary_error ? 0.5 : 1 }}
          required
          disabled={!isEditing}
          value={localFields.summary}
          onChange={handleFieldChange("summary")}
          helperText={errors?.summary_error}
          InputProps={{
            readOnly: !isEditing, // Toggle read-only based on edit mode
          }}
        />
      </FormControl> */}
      <OutlinedInput
        size="small"
        value={localFields.summary}
        onChange={handleFieldChange("summary")}
        fullWidth
        required
        placeholder="Summary"
        name="summary"
        disabled={!isEditing}
        onFocus={summaryFocusHandler}
        onBlur={summaryBlurHandler}
        margin="normal"
        sx={{ mb: errors?.summary_error ? 0.5 : 1 }}
        inputProps={{ readOnly: !isEditing }}
      />
      {errors?.summary_error && (
        <Typography variant="body2" color="error" sx={{ marginBottom: 1 }}>
          {errors.summary_error}
        </Typography>
      )}
      <OutlinedInput
        size="small"
        value={localFields.description}
        onChange={handleFieldChange("description")}
        fullWidth
        required
        name="description"
        disabled={!isEditing}
        onFocus={descriptionFocusHandler}
        onBlur={descriptionBlurHandler}
        placeholder="Description"
        margin="normal"
        sx={{ mb: errors?.description_error ? 0.5 : 1 }}
        inputProps={{ readOnly: !isEditing }}
      />
      {errors?.description_error && (
        <Typography variant="body2" color="error" sx={{ marginBottom: 1 }}>
          {errors.description_error}
        </Typography>
      )}
      <OutlinedInput
        size="small"
        fullWidth
        required
        value={localFields.acceptance_criteria}
        name="acceptance_criteria"
        disabled={!isEditing}
        onChange={handleFieldChange("acceptance_criteria")}
        onFocus={acceptanceCriteriaFocusHandler}
        onBlur={acceptanceCriteriaBlurHandler}
        placeholder="Acceptance Criteria"
        margin="normal"
        sx={{ mb: "1rem" }}
        multiline
        minRows={10}
        maxRows={15}
        inputProps={{ readOnly: !isEditing }}
      />
      {errors?.ac_error && (
        <Typography variant="body2" color="error" sx={{ marginBottom: 1 }}>
          {errors.ac_error}
        </Typography>
      )}
    </Paper>
  );
}

const OptimizedRequirementDetails = withRequirementDetails(RequirementDetails);

export default OptimizedRequirementDetails;
