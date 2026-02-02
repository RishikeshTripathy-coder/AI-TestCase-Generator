import { Box, Typography, Button, Paper, IconButton } from "@mui/material";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import CloseIcon from "@mui/icons-material/Close";
import styled from "@emotion/styled";
import { mapContextToType } from "../utils/mapContextToType";
import config from "../config";
import { useAlert } from "../hooks/useAlert";
import AlertMsg from "./alerts/AlertMsg";
import { useState, useEffect, memo } from "react";
import { useStoriesContext } from "../hooks/useStoriesContext";

const VisuallyHiddenInput = styled("input")({
  clip: "rect(0 0 0 0)",
  clipPath: "inset(50%)",
  height: 1,
  overflow: "hidden",
  position: "absolute",
  bottom: 0,
  left: 0,
  whiteSpace: "nowrap",
  width: 1,
});
// Styled file item container
const FileItem = styled(Paper)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  padding: theme.spacing(1),
  paddingLeft: theme.spacing(2),
  borderRadius: 8,
  backgroundColor: theme.palette.grey[100],
  maxWidth: "100%",
  overflow: "hidden",
}));

const FileName = styled("span")({
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
  maxWidth: "260px",
  display: "inline-block",
});

// Upload Test Cases HOC
const withUploadTestCases = (Component) => {
  const MemoizedComponent = memo(Component);
  return (props) => {
    const { setFileContext, fileContext } = useStoriesContext();
    return (
      <MemoizedComponent
        {...props}
        fileContext={fileContext}
        setFileContext={setFileContext}
      />
    );
  };
};

function UploadTestCases({ selectedContext, setFileContext, fileContext }) {
  console.count("Upload Context File");
  // const { setFileContext, fileContext } = useStoriesContext();
  const { open, setOpen } = useAlert();
  const [msg, setMsg] = useState("");
  const [severity, setSeverity] = useState("success");
  const [selectedFiles, setSelectedFiles] = useState([]);

  // Keep the local selectedFiles in sync with the shared fileContext.
  // When fileContext is cleared (for example after generation completes),
  // clear the local selectedFiles so the uploaded filename UI is removed.
  useEffect(() => {
    if (!fileContext) {
      setSelectedFiles([]);
    }
  }, [fileContext]);

  // function to handle file change
  const handleFileChange = async (event) => {
    try {
      const input = event.target;
      // Ensure files were selected
      if (!input.files || input.files.length === 0) {
        alert("No file selected");
        return;
      }
      // converting FileList to an array
      const files = Array.from(input.files);
      input.value = ""; // reset the input value to allow re-uploading the same file if needed
      console.log("files selected:", files);
      if (files.length > 0) {
        const file = files[0];

        // Validate file type based on selectedContext
        if (selectedContext === "Upload JSON") {
          if (!file.name.toLowerCase().endsWith(".json")) {
            setOpen(true);
            setSeverity("error");
            setMsg(
              "Error: Please upload a JSON file. Other file types are not supported for JSON context."
            );
            return;
          }
        } else if (selectedContext === "Upload YAML") {
          if (!file.name.toLowerCase().match(/\.(yaml|yml)$/)) {
            setOpen(true);
            setSeverity("error");
            setMsg(
              "Error: Please upload a YAML file. Other file types are not supported for YAML context."
            );
            return;
          }
        } else if (selectedContext === "Upload Plain Text") {
          // if (!file.name.toLowerCase().match(/\.(pdf|doc|docx)$/))
          if (!file.name.toLowerCase().match(/\.(txt|text)$/)) {
            setOpen(true);
            setSeverity("error");
            setMsg(
              "Error: Please upload a Text file. Other file types are not supported for document context."
            );
            return;
          }
        } else if (selectedContext === "Upload Existing Test Case") {
          if (!file.name.toLowerCase().match(/\.(csv|xls|xlsx)$/)) {
            setOpen(true);
            setSeverity("error");
            setMsg(
              "Error: Please upload a CSV, XLS, or XLSX file. Other file types are not supported for test case imports."
            );
            return;
          }
        } else if (selectedContext === "Upload BRD") {
          if (!file.name.toLowerCase().match(/\.(pdf|docx|png|jpg|jpeg|bmp|tiff|webp|gif)$/)) {
            setOpen(true);
            setSeverity("error");
            setMsg(
              "Error: Please upload a PDF, DOCX file or Image (PNG, JPG, JPEG, BMP, TIFF, WEBP, GIF) for BRD. Other file types are not supported for BRD."
            );
            return;
          }
        }

        setSelectedFiles(files);
        const formData = new FormData();
        formData.append("context_type", mapContextToType(selectedContext));
        if (
          [
            "Upload JSON",
            "Upload YAML",
            "Upload Plain Text",
            "Upload Existing Test Case",
            "Upload BRD",
          ].includes(selectedContext)
        ) {
          formData.append("file", files[0]); // single file upload (BRD supported)
        }

        // // If it's a scrape URL
        // if (selectedContext === "Scrape URL") {
        //   formData.append("url", "https://your-url-to-scrape");
        // }
        const response = await fetch(`${config.fetchUrl}/upload_context`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error("Failed to upload context");
        }

        const data = await response.json();
        console.log("Upload successful:", data);
        setOpen(true);
        setSeverity("success");
        setMsg(data.message);
        setFileContext(data);
      }
    } catch (error) {
      console.log(error);
      setMsg(error.message);
    }
  };

  const isBrowseBtnDisabled =
    selectedContext === "No Context" ||
    selectedContext === "Scrape URL" ||
    selectedContext === "Manual Input";

  const uploadLabel = () => {
    if (
      selectedContext === "No Context" ||
      selectedContext === "Scrape URL" ||
      selectedContext === "Manual Input"
    ) {
      return "Upload Context File";
    } else {
      return selectedContext;
    }
  };

  // Function to return accept MIME type(s) based on selected context
  const getAcceptedFileTypes = () => {
    switch (selectedContext) {
      case "Upload JSON":
        return ".json,application/json";
      case "Upload YAML":
        return ".yaml,.yml,text/yaml";
      case "Upload Plain Text":
        return ".txt,.text,text/plain";
      case "Upload Existing Test Case":
        return ".csv, .xls, .xlsx, text/csv, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
      case "Upload BRD":
        return ".pdf,.docx,.png,.jpg,.jpeg,.bmp,.tiff,.webp,.gif,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/png,image/jpeg,image/bmp,image/tiff,image/webp,image/gif";
      default:
        return "";
    }
  };

  const handleRemoveFile = (indexToRemove) => {
    setSelectedFiles((prev) =>
      prev.filter((_, index) => index !== indexToRemove)
    );
    setFileContext(null);
  };

  return (
    <Paper variant="outlined" sx={{ p: 2, bgcolor: "white", height: "95%" }}>
      <AlertMsg msg={msg} open={open} setOpen={setOpen} severity={severity} />
      <Typography variant="h6" fontWeight={"bold"} gutterBottom>
        {uploadLabel()}
      </Typography>
      <Button
        component="label"
        disabled={isBrowseBtnDisabled || Boolean(fileContext)}
        role={undefined}
        variant="outlined"
        tabIndex={-1}
        startIcon={<InsertDriveFileOutlinedIcon />}
      >
        Browse files
        <VisuallyHiddenInput
          type="file"
          accept={getAcceptedFileTypes()}
          onChange={handleFileChange}
          // multiple
        />
      </Button>
      
      {/* Show supported file types info */}
      {selectedContext === "Upload BRD" && (
        <Typography variant="body2" sx={{ mt: 2, color: "text.secondary" }}>
          📄 Supported formats: PDF, DOCX, PNG, JPG, JPEG, BMP, TIFF, WEBP, GIF
          <br />
          📷 Images will be scanned using OCR to extract text and context
        </Typography>
      )}
      
      {selectedContext === "Upload JSON" && (
        <Typography variant="body2" sx={{ mt: 2, color: "text.secondary" }}>
          Supported format: JSON files only
        </Typography>
      )}
      
      {selectedContext === "Upload YAML" && (
        <Typography variant="body2" sx={{ mt: 2, color: "text.secondary" }}>
          Supported formats: YAML (.yaml, .yml) files
        </Typography>
      )}
      
      {selectedContext === "Upload Plain Text" && (
        <Typography variant="body2" sx={{ mt: 2, color: "text.secondary" }}>
          Supported formats: Plain text (.txt) files
        </Typography>
      )}
      
      {selectedContext === "Upload Existing Test Case" && (
        <Typography variant="body2" sx={{ mt: 2, color: "text.secondary" }}>
          Supported formats: CSV, XLS, XLSX spreadsheets
        </Typography>
      )}

      {/* File preview with remove icons */}
      {selectedFiles.length > 0 && (
        <Box display="flex" flexDirection="column" gap={1}>
          <Typography variant="subtitle2">Uploaded File:</Typography>
          {selectedFiles.map((file, index) => (
            <FileItem elevation={0} key={index}>
              <FileName title={file.name}>{file.name}</FileName>
              <IconButton
                size="small"
                onClick={() => handleRemoveFile(index)}
                aria-label={`Remove ${file.name}`}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </FileItem>
          ))}
        </Box>
      )}
    </Paper>
  );
}

const OptimizedUploadTestCases = withUploadTestCases(UploadTestCases);
export default OptimizedUploadTestCases;
