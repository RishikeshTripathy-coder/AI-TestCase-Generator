import {
  Typography,
  TextField,
  Button,
  Paper,
  MenuItem,
  IconButton,
  Tooltip,
  Box,
} from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import {
  useState,
  // useImperativeHandle,
  useRef,
  forwardRef,
  useEffect,
  memo,
} from "react";
import { useErrors } from "../hooks/useErrors";
// import { isValidRequirement } from "../utils/validRequirementsCheck";
import config from "../config";
import { useAlert } from "../hooks/useAlert";
import { useStoriesContext } from "../hooks/useStoriesContext";
import AlertMsg from "./alerts/AlertMsg";

const context = [
  { value: "No Context", label: "No Context" },
  { value: "Upload JSON", label: "Upload JSON" },
  { value: "Upload YAML", label: "Upload YAML" },
  { value: "Upload Plain Text", label: "Upload Plain Text" },
  { value: "Upload BRD", label: "Upload BRD (PDF/DOCX)" },
  { value: "Scrape URL", label: "Scrape URL" },
  // { value: "Manual Input", label: "Manual Input" },
  { value: "Upload Existing Test Case", label: "Upload Existing Test Case" },
];

// ContextSetup HOC
const withContextSetup = (Component) => {
  const MemoizedComponent = memo(Component);
  return (props) => {
    const { fileContext } = useStoriesContext();
    return <MemoizedComponent {...props} fileContext={fileContext} />;
  };
};

const ContextSetup = forwardRef(
  ({ selectedContext, handleSelectContext, fileContext }, ref) => {
    console.count("ContextSetup");
    // const [manualInput, setManualInput] = useState("");
    // const { fileContext } = useStoriesContext();
    const scrapeUrlRef = useRef(null);
    const { open, setOpen } = useAlert();
    const [msg, setMsg] = useState("");
    // severity for AlertMsg: 'success' | 'error' (default 'success')
    const [severity, setSeverity] = useState("success");
    const [loading, setLoading] = useState(false);
    const { errors, setErrors, inputBlurHandler, inputFocusHandler } =
      useErrors();

    // useEffect to clear the selectedContext label when fileContext is empty
    useEffect(() => {
      if (!fileContext) {
        handleSelectContext({ target: { value: "No Context" } });
      }
    }, [fileContext, handleSelectContext]);

    // Clear manual input and errors when selectedContext changes
    // useEffect(() => {
    //   setManualInput("");
    //   setErrors((prev) => ({ ...prev, manual_input_error: "" }));
    // }, [selectedContext, setErrors]);

    // Function to handle changes in the Manual Input field
    // const manualInputFocusHandler = () => {
    //   if (errors?.manual_input_error) {
    //     inputFocusHandler("manual_input_error");
    //   }
    // };
    // const manualInputBlurHandler = (e) => {
    //   const inputValue = e.target.value;
    //   // Check if the manual input requirement meets the valid requirements
    //   const isValidRequirements = isValidRequirement(inputValue);
    //   if (!isValidRequirements.valid) {
    //     inputBlurHandler("manual_input_error", isValidRequirements.message);
    //   } else {
    //     // Clear error if valid
    //     inputBlurHandler("manual_input_error", "");
    //   }
    // };

    // const handleManualInputChange = (e) => {
    //   setManualInput(e.target.value);
    // };

    // useImperativeHandle(ref, () => ({
    //   getManualInput: () => manualInput,
    // }));

    // function to handle Scrape URL button click and validate errors
    const scrapeUrlHandler = async () => {
      const url = scrapeUrlRef.current.value;
      console.log(scrapeUrlRef.current.value);
      if (!url || url.trim() === "") {
        setErrors((prev) => ({
          ...prev,
          scrape_url_error: "Scrape URL cannot be empty.",
        }));
        return;
      }
      try {
        setLoading(true);
        const resp = await fetch(`${config.fetchUrl}/scrape_url`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ url }),
        });
        const data = await resp.json();
        if (resp.ok) {
          console.log("Scraped URL data:", data);
          setSeverity("success");
          setOpen(true);
          // prefer an explicit message from the backend, fall back to generic
          setMsg(data?.message || "Scrape successful");
          ref.current = data;
          // setFileContext(data.context);
        } else {
          console.log("Error scraping URL:", data);
          setSeverity("error");
          // FastAPI often returns { detail: '...' }
          const errorDetail =
            data?.detail || data?.message || JSON.stringify(data);
          setMsg(`Error scraping URL: ${errorDetail}`);
          setOpen(true);
        }
      } catch (error) {
        console.log("Error scraping URL:", error);
        setSeverity("error");
        setMsg(error?.message || String(error));
        setOpen(true);
      } finally {
        setLoading(false);
      }
    };

    const scrapeUrlFocusHandler = () => {
      if (errors?.scrape_url_error) {
        inputFocusHandler("scrape_url_error");
      }
    };
    const scrapeUrlBlurHandler = (e) => {
      const url = e.target.value;
      // Basic URL format validation
      try {
        new URL(url);
        // Clear error if valid
        inputBlurHandler("scrape_url_error", "");
      } catch (e) {
        console.log("Invalid URL format:", e);
        inputBlurHandler("scrape_url_error", "Please enter a valid URL.");
      }
    };

    return (
      <Paper variant="outlined" sx={{ p: 2, bgcolor: "white", height: "95%" }}>
        <AlertMsg msg={msg} open={open} setOpen={setOpen} severity={severity} />
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <Typography variant="h6" fontWeight={"bold"} gutterBottom>
            Context Setup
          </Typography>
          <Tooltip
            title="Add extra context to guide your test case generation. Supports JSON, YAML, plain text, or web scraping inputs. For examples of each type, refer → Sample Context Templates in navigation."
            arrow
            placement="top"
            sx={{ mb: "5px" }}
          >
            <IconButton size="small" color="primary">
              <HelpOutlineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
        {/* <Select fullWidth size="small" defaultValue="TESTAUTO-225">
        <MenuItem value="TESTAUTO-225">
          TESTAUTO-225 - test ai prototype
        </MenuItem>
      </Select> */}
        <TextField
          size="small"
          fullWidth
          select
          label="Select Context"
          value={selectedContext}
          onChange={handleSelectContext}
          disabled={Boolean(fileContext)}
        >
          {context?.map((ctx) => {
            return (
              <MenuItem key={ctx.value} value={ctx.value}>
                {ctx.label}
              </MenuItem>
            );
          })}
        </TextField>
        {selectedContext === "Scrape URL" && (
          <>
            <TextField
              size="small"
              fullWidth
              label="Scrape URL"
              inputRef={scrapeUrlRef}
              disabled={Boolean(fileContext)}
              margin="normal"
              onFocus={scrapeUrlFocusHandler}
              onBlur={scrapeUrlBlurHandler}
              error={Boolean(errors?.scrape_url_error)}
              helperText={errors?.scrape_url_error}
            />
            <Button
              variant="contained"
              onClick={scrapeUrlHandler}
              size="small"
              color="primary"
              disabled={
                Boolean(errors?.scrape_url_error) || Boolean(fileContext)
              }
              loading={loading}
              loadingPosition="end"
            >
              Scrape
            </Button>
          </>
        )}
        {/* {selectedContext === "Manual Input" && (
          <TextField
            size="small"
            fullWidth
            label="Manual Input"
            multiline
            rows={4}
            margin="normal"
            value={manualInput}
            onChange={handleManualInputChange}
            onFocus={manualInputFocusHandler}
            onBlur={manualInputBlurHandler}
            error={Boolean(errors?.manual_input_error)}
            helperText={errors?.manual_input_error}
          />
        )} */}
      </Paper>
    );
  }
);

const OptimizedContextSetupComponent = withContextSetup(ContextSetup);

export default OptimizedContextSetupComponent;
