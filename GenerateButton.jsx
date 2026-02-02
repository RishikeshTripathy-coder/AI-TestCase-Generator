import { Button } from "@mui/material";
import { useStoriesContext } from "../../hooks/useStoriesContext";
import config from "../../config";
import { memo, useState } from "react";
import AlertMsg from "../alerts/AlertMsg";

// Generate Button HOC
const withGenerateButton = (Component) => {
  const MemoizedComponent = memo(Component);
  return (props) => {
    const {
      selectedStory,
      setTestScripts,
      fileContext,
      setFileContext,
      setIsTestScriptGenerating,
    } = useStoriesContext();
    return (
      <MemoizedComponent
        {...props}
        selectedStory={selectedStory}
        setTestScripts={setTestScripts}
        fileContext={fileContext}
        setFileContext={setFileContext}
        setIsTestScriptGenerating={setIsTestScriptGenerating}
      />
    );
  };
};

const GenerateButton = ({
  manualInputRef,
  scrapeUrlTextRef,
  generationType,
  selectedStory,
  setTestScripts,
  fileContext,
  setFileContext,
  setIsTestScriptGenerating,
}) => {
  console.count("GenerateButton");
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  
  const generateTestScriptsHandler = async () => {
    try {
      let context_json = {};

      // 🧠 Manual input (include regardless of generationType if provided)
      const manualInput = manualInputRef?.current?.value?.trim();
      if (manualInput) {
        context_json["manual_input"] = manualInput;
      } else if (generationType === "manual") {
        // require manual input in manual generation mode
        console.log("No manual input provided");
        alert("Please provide manual input.");
        return;
      }

      // 🧠 Case 2: File uploaded (from fileContext)
      if (fileContext && Object.keys(fileContext).length > 0) {
        // fileContext is the response from /upload_context
        // so it looks like { filename: "...", context: "...", message: "..." }

        // If it's a JSON file, parse the context string safely
        if (fileContext.filename?.endsWith(".json")) {
          try {
            context_json["file_context"] = JSON.parse(fileContext.context);
          } catch (e) {
            console.error(
              "Failed to parse JSON file context, treating as text",
              e
            );
            context_json["file_context"] = fileContext.context;
          }
        } else {
          // For YAML, TXT, CSV, etc.
          context_json["file_context"] = fileContext.context;
        }
      }
      // 🧠 Case 3: Context from Scraped URL
      if (
        generationType === "automate" &&
        scrapeUrlTextRef?.current?.isUrlScraped
      ) {
        context_json["scraped_url_content"] =
          scrapeUrlTextRef?.current?.context?.trim();
      }
      setLoading(true);
      setIsTestScriptGenerating(true);
      let endpoint = "generate_test_scripts";
      let body = JSON.stringify({
        description: selectedStory?.description,
        requirement_text: selectedStory?.acceptance_criteria,
        context_json: context_json,
      });
      if (generationType === "manual") {
        // User is generating the test scripts manually
        console.log("Generating test scripts with manual input...");
        endpoint = "generate-test-script-from-manual-input";
        body = JSON.stringify({
          manual_input: context_json["manual_input"],
          context: context_json["file_context"] || "No context provided",
        });
      }
      const resp = await fetch(`${config.fetchUrl}/${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: body,
      });
      const data = await resp.json();
      if (resp.ok) {
        setTestScripts(data.test_steps || []);
        setOpen(true);
        setFileContext(null); // Clear file context after generation
      } else {
        console.log("Error while generating test scripts:", data);
      }
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
      setIsTestScriptGenerating(false);
    }
  };
  return (
    <>
      <AlertMsg
        msg="Test Scripts Generated Successfully"
        open={open}
        setOpen={setOpen}
      />
      <Button
        onClick={generateTestScriptsHandler}
        variant="contained"
        loading={loading}
        loadingPosition="end"
        size="small"
        disabled={generationType === "automate" && !selectedStory?.key}
      >
        Generate Test Cases
      </Button>
    </>
  );
};

const OptimizedGenerateButton = withGenerateButton(GenerateButton);
export default OptimizedGenerateButton;
