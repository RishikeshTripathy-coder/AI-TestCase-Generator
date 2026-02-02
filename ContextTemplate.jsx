import { Box, Typography, Snackbar, Alert } from "@mui/material";
import { useState } from "react";
import CopyableTemplate from "../components/template/CopyableTemplate";
import useClipboard from "../hooks/useClipboard";
import { TEMPLATE_DATA } from "../utils/templateData";

const ContextTemplate = () => {
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const { copyToClipboard } = useClipboard();

  const handleCopy = async (text, type) => {
    try {
      await copyToClipboard(text);
      setSnackbar({
        open: true,
        message: `${type} template copied to clipboard`,
        severity: "success",
      });
    } catch {
      setSnackbar({
        open: true,
        message: "Failed to copy to clipboard",
        severity: "error",
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  return (
    <Box sx={{ padding: 4 }}>
      <Typography variant="h5" gutterBottom>
        Context File Setup – Examples & Templates
      </Typography>

      <Typography variant="body1" paragraph>
        Use these templates to provide structured context that helps the AI
        generate accurate and executable Jira test cases. You can upload JSON,
        YAML, or plain text files.
      </Typography>

      {TEMPLATE_DATA.map((template) => (
        <CopyableTemplate
          key={template.id}
          title={template.title}
          icon={template.icon}
          content={template.content}
          onCopy={handleCopy}
        />
      ))}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={handleCloseSnackbar}
          sx={{ width: "100%" }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ContextTemplate;
