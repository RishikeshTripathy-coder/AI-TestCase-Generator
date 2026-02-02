import {
  TextField,
  Button,
  Typography,
  Paper,
  OutlinedInput,
  Grid,
  MenuItem,
  FormControl,
} from "@mui/material";
import PasswordField from "./input-field/PasswordField";
import { useErrors } from "../hooks/useErrors";
import { fetchJiraUserStories } from "../api/fetchJiraUserStories";
import { memo, useState } from "react";
import AlertMsg from "./alerts/AlertMsg";
import { useStoriesContext } from "../hooks/useStoriesContext";

// JiraSetup HOC
const withJiraSetup = (Component) => {
  const MemoizedComponent = memo(Component);
  return (props) => {
    const { setUserStories, isTestScriptGenerating } = useStoriesContext();
    return (
      <MemoizedComponent
        {...props}
        isTestScriptGenerating={isTestScriptGenerating}
        setUserStories={setUserStories}
      />
    );
  };
};

function JiraSetup({ setUserStories, isTestScriptGenerating }) {
  console.count("JiraSetup");
  const { errors, inputBlurHandler, inputFocusHandler } = useErrors();
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  // Function to get all the user stories from Jira
  const getUserStoriesHandler = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const jiraAPIKey = fd.get("jira_api_key");
    const jqlQuery = fd.get("jql_query");
    if (
      !jiraAPIKey ||
      jiraAPIKey.trim().length === 0 ||
      !jqlQuery ||
      jqlQuery.trim().length === 0
    ) {
      alert("Invalid fields in Jira Setup section!!!");
      return;
    }
    try {
      setLoading(true);
      const resp = await fetchJiraUserStories(jiraAPIKey, jqlQuery);
      if (resp?.length > 0) {
        setUserStories(resp);
        setOpen(true);
      }
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  // function that handles the error message if the input field is focussed
  const jqlFieldFocusHandler = () => {
    if (errors.jql_query_error) {
      inputFocusHandler("jql_query_error");
    }
  };

  // function that handles the error message if the input field is blurred
  const jqlFieldBlurHandler = (e) => {
    const inputValue = e.target.value;
    if (inputValue.trim().length < 10) {
      inputBlurHandler("jql_query_error", "Invalid JQL query");
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: "white" }}>
      <Typography variant="h6" fontWeight={"bold"}>
        Jira Setup
      </Typography>
      <AlertMsg msg={"Got the user stories"} open={open} setOpen={setOpen} />
      <form onSubmit={getUserStoriesHandler}>
        <Grid container spacing={2}>
          {/* <TextField fullWidth label="Jira Base URL" margin="normal" /> */}
          <PasswordField />
          <Grid size={{ xs: 12, sm: 6, md: 7 }}>
            <FormControl fullWidth variant="outlined" margin="normal">
              <TextField
                size="small"
                fullWidth
                name="jql_query"
                label="JQL Query"
                onFocus={jqlFieldFocusHandler}
                onBlur={jqlFieldBlurHandler}
                error={Boolean(errors?.jql_query_error)}
                required
                helperText={errors?.jql_query_error}
              />
            </FormControl>
          </Grid>
        </Grid>
        <Button
          variant="contained"
          loading={loading}
          loadingPosition="end"
          disabled={isTestScriptGenerating ? true : false}
          type="submit"
          size="small"
          color="primary"
          sx={{ mt: 3 }}
        >
          Get User Stories
        </Button>
      </form>
    </Paper>
  );
}

const OptimizedJiraSetup = withJiraSetup(JiraSetup);
export default OptimizedJiraSetup;
