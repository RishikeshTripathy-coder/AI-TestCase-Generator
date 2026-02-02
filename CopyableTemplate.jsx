import { Box, Typography, Paper, IconButton, Tooltip } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import PropTypes from "prop-types";

const JSON_FOR_API = `For API
  {
    "moduleName": "UserAuth API",
    "type": "api",
    "use_gherkin": false,
    "description": "API for handling user authentication using POST method",
    "api": {
      "endpoint": "/api/auth/login",
      "methods": ["POST"],
      "requestParams": ["username", "password"],
      "responseKeys": ["token", "user_id", "expires_in"],
      "validations": ["status_code == 200", "response contains token"]
    }
  }`;

const CopyableTemplate = ({ title, icon, content, onCopy }) => {
  return (
    <Paper sx={{ padding: 2, marginBottom: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Typography variant="h6">
          {icon} {title}
        </Typography>
        <Tooltip title={`Copy ${title} template`}>
          <IconButton
            onClick={() => {
              if (title === "JSON") {
                onCopy(content + "\n\n" + JSON_FOR_API, title);
              } else {
                onCopy(content, title);
              }
            }}
            size="small"
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <pre
        style={{
          background: "#f4f4f4",
          padding: "1em",
          borderRadius: "8px",
          overflowX: "auto",
        }}
      >
        {content}
      </pre>
      {title === "JSON" && (
        <pre
          style={{
            background: "#f4f4f4",
            padding: "1em",
            borderRadius: "8px",
            overflowX: "auto",
            marginTop: "1em",
          }}
        >
          {JSON_FOR_API}
        </pre>
      )}
    </Paper>
  );
};

CopyableTemplate.propTypes = {
  title: PropTypes.string.isRequired,
  icon: PropTypes.string.isRequired,
  content: PropTypes.string.isRequired,
  onCopy: PropTypes.func.isRequired,
};

export default CopyableTemplate;
