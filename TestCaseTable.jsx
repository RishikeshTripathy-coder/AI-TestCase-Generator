import {
  Typography,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Button,
  Paper,
  TablePagination,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemText,
  Box,
  Checkbox,
} from "@mui/material";
import { ExpandMore, ExpandLess } from "@mui/icons-material";
import { useStoriesContext } from "../hooks/useStoriesContext";
import { memo, useEffect, useMemo, useState } from "react";
import config from "../config";
import AlertMsg from "./alerts/AlertMsg";

// TestCaseTable HOC
const withTestCaseTable = (Component) => {
  const MemoizedComponent = memo(Component);
  return (props) => {
    const { testScripts, selectedStory } = useStoriesContext();
    return (
      <MemoizedComponent
        {...props}
        testScripts={testScripts}
        selectedStory={selectedStory}
      />
    );
  };
};

const TestCaseTable = ({ testScripts, selectedStory }) => {
  console.count("TestCaseTable");
  // const { testScripts, selectedStory } = useStoriesContext();

  // state to hold loading status for upload button
  const [uploading, setUploading] = useState(false);
  // state to hold alert for successful generation
  const [open, setOpen] = useState(false);

  // state to hold the test scripts message
  const [message, setMessage] = useState("");

  // console.log(typeof testScripts);
  console.log(testScripts);
  // Backend returns an array of test case objects. We'll use them directly as rows.
  const rows = useMemo(() => testScripts || [], [testScripts]);
  // track expanded rows for showing Steps
  const [expanded, setExpanded] = useState({});
  // track selected test cases for upload
  const [selectedCases, setSelectedCases] = useState({});

  const toggleExpanded = (idx) => {
    setExpanded((prev) => {
      console.log("prev:", prev);
      return { ...prev, [idx]: !prev[idx] };
    });
  };
  const [page, setPage] = useState(0);
  const rowsPerPage = 10; // fixed as requested

  // reset page to 0 when rows change (e.g., new scripts loaded)
  useEffect(() => {
    setPage(0);
  }, [testScripts]);

  const paginatedRows = useMemo(() => {
    if (!rows) return [];
    const start = page * rowsPerPage;
    return rows.slice(start, start + rowsPerPage);
  }, [rows, page]);

  const downloadHandler = async () => {
    try {
      const resp = await fetch(`${config.fetchUrl}/download`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(testScripts),
      });
      if (!resp.ok) {
        throw new Error("Error while downloading excel file");
      }
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = "test_cases.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();

      // Cleanup the object URL
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.log(error);
    }
  };

  // Handle individual checkbox change
  const handleCheckboxChange = (globalIndex) => {
    setSelectedCases((prev) => ({
      ...prev,
      [globalIndex]: !prev[globalIndex],
    }));
  };

  // Handle select all checkbox
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      // Select all test cases
      const newSelected = {};
      rows.forEach((_, idx) => {
        newSelected[idx] = true;
      });
      setSelectedCases(newSelected);
    } else {
      // Deselect all
      setSelectedCases({});
    }
  };

  // Get selected test cases
  const getSelectedTestCases = () => {
    return rows
      .map((row, idx) => (selectedCases[idx] ? row : null))
      .filter((row) => row !== null);
  };

  // Check if all cases are selected
  const isAllSelected = rows.length > 0 && Object.values(selectedCases).filter(Boolean).length === rows.length;
  
  // Count of selected cases
  const selectedCount = Object.values(selectedCases).filter(Boolean).length;

  const uploadTestScriptsToJiraHandler = async () => {
    try {
      // Get the test cases to upload
      let casesToUpload = testScripts;
      
      // If specific cases are selected, use only those
      if (selectedCount > 0) {
        casesToUpload = getSelectedTestCases();
      }

      if (casesToUpload.length === 0) {
        alert("Please select at least one test case to upload.");
        return;
      }

      setUploading(true);
      let steps;
      if (config.uploadActualTestCases === "true") {
        console.log(`Uploading ${casesToUpload.length} actual test cases to Jira`);
        steps = casesToUpload;
      } else {
        console.log(`Uploading ${casesToUpload.length} dummy test cases to Jira`);
        // Upload dummy steps which contains an array of objects with action, data, expected_result as some random text
        steps = [
          {
            "Test Case ID": "TC_001",
            Title:
              "Display error message and ServiceNow link on OpenAI response timeout",
            Description:
              "Verifies that a standardized error message with clear error nature and a ServiceNow incident link is shown when the conversion fails due to an OpenAI API timeout.",
            Steps: [
              {
                "Step Number": 1,
                Action:
                  "Send POST request to /api/auth/login with valid credentials",
                Data: '"username":"qa_user","password":"Passw0rd!"',
                "Expected Result":
                  "Authentication succeeds with status 200 and a token is returned in the response payload",
              },
              {
                "Step Number": 2,
                Action: "Open the SAS-to-R conversion page while authenticated",
                Data: "NA",
                "Expected Result":
                  "Conversion page loads successfully and displays file upload control and convert action",
              },
              {
                "Step Number": 3,
                Action: "Upload a valid SAS file for conversion",
                Data: "sample_valid.sas7bdat",
                "Expected Result":
                  "File is accepted and displayed as ready for conversion",
              },
              {
                "Step Number": 4,
                Action: "Start the conversion process",
                Data: "NA",
                "Expected Result":
                  "Conversion begins and a processing indicator appears",
              },
              {
                "Step Number": 5,
                Action: "Simulate OpenAI API timeout during conversion",
                Data: "NA",
                "Expected Result":
                  "Conversion fails and an error message banner appears",
              },
              {
                "Step Number": 6,
                Action: "Observe the error banner content",
                Data: "NA",
                "Expected Result":
                  'Error banner displays: "We encountered an issue while converting your file. We apologize for the inconvenience. Please reach out to our support team for further help." and includes a detail stating the error nature such as "Request timed out"',
              },
              {
                "Step Number": 7,
                Action:
                  "Verify suggestion and ServiceNow incident link presence in the banner",
                Data: "NA",
                "Expected Result":
                  "Banner suggests next steps to contact support and contains a clickable link labeled for ServiceNow incident reporting",
              },
              {
                "Step Number": 8,
                Action: "Click the ServiceNow incident link in the banner",
                Data: "NA",
                "Expected Result":
                  "A new page opens to the organization's ServiceNow incident reporting page and displays the incident creation form without errors",
              },
            ],
          },
          {
            "Test Case ID": "TC_002",
            Title:
              "Display error message for OpenAI API HTTP 500 during conversion",
            Description:
              "Verifies that a response failure from the OpenAI API returns the required error message with the nature of the error, suggests next steps, and shows a ServiceNow link.",
            Steps: [
              {
                "Step Number": 1,
                Action:
                  "Launch the application and navigate to the conversion page",
                Data: "NA",
                "Expected Result":
                  "The conversion page loads successfully with controls to upload a file and start conversion",
              },
              {
                "Step Number": 2,
                Action: "Upload a valid SAS file",
                Data: "sample_valid.sas",
                "Expected Result":
                  "The file is accepted and listed as ready for conversion",
              },
              {
                "Step Number": 3,
                Action:
                  "Configure the test environment to simulate an OpenAI API HTTP 500 response failure",
                Data: "mock_error=HTTP_500",
                "Expected Result":
                  "The system is set to return HTTP 500 on the next conversion request",
              },
              {
                "Step Number": 4,
                Action: "Start the conversion",
                Data: "NA",
                "Expected Result":
                  "The conversion initiates, then fails due to simulated HTTP 500",
              },
              {
                "Step Number": 5,
                Action:
                  "Observe the error notification displayed on the screen",
                Data: "NA",
                "Expected Result":
                  'An error message is displayed containing the exact text: "We encountered an issue while converting your file. We apologize for the inconvenience. Please reach out to our support team for further help."',
              },
              {
                "Step Number": 6,
                Action:
                  "Check the error details area or label within the error notification",
                Data: "NA",
                "Expected Result":
                  'The nature of the error is clearly stated, such as "Error type: Response Failure (HTTP 500)" and optionally includes brief details like "Internal Server Error"',
              },
              {
                "Step Number": 7,
                Action:
                  "Verify the presence of a ServiceNow incident link in the error notification",
                Data: "NA",
                "Expected Result":
                  'A clickable link labeled appropriately for raising an incident (e.g., "Raise an incident in ServiceNow") is visible',
              },
            ],
          },
        ];
      }
      // const payload = {
      //   summary: `${selectedStory.summary}`,
      //   steps: steps,
      // };
      const payload = {
        summary: `${selectedStory.summary}`,
        testScripts: steps,
      };
      console.log("Uploading to Jira with payload:", payload);
      const resp = await fetch(
        `${config.fetchUrl}/upload-test-scripts-to-jira`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );
      if (!resp.ok) {
        throw new Error("Error while uploading test scripts to Jira");
      }
      const data = await resp.json();
      console.log("Upload to Jira response:", data);
      setUploading(false);
      setMessage(data);
      setOpen(true);
      // Reset selection after successful upload
      setSelectedCases({});
    } catch (error) {
      console.log(error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 3, mb: 3, bgcolor: "white" }}>
      <AlertMsg
        msg={
          message?.message ? (
            <span>
              <b>{message.message}</b>
              <br />
              URL:{" "}
              <a href={message.test_execution_url} target="_blank">
                {message.test_execution_url}
              </a>
            </span>
          ) : (
            "Test Scripts Uploaded to Jira Successfully"
          )
        }
        open={open}
        setOpen={setOpen}
      />
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h6" fontWeight={"bold"}>
          Test Case Output
        </Typography>
      </Box>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell padding="checkbox">
              <Checkbox
                indeterminate={selectedCount > 0 && !isAllSelected}
                checked={isAllSelected}
                onChange={handleSelectAll}
                title="Select all test cases"
              />
            </TableCell>
            <TableCell />
            <TableCell>Test Case ID</TableCell>
            <TableCell>Title</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Steps</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {paginatedRows.map((row, i) => {
            const globalIndex = page * rowsPerPage + i;
            // console.log("globalIndex", globalIndex);
            return (
              <>
                <TableRow key={i}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedCases[globalIndex] || false}
                      onChange={() => handleCheckboxChange(globalIndex)}
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => toggleExpanded(globalIndex)}
                    >
                      {expanded[globalIndex] ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </TableCell>
                  <TableCell>
                    {row["Test Case ID"] || row.id || `#${globalIndex + 1}`}
                  </TableCell>
                  <TableCell
                    sx={{
                      maxWidth: 240,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    <Typography variant="subtitle2">{row.Title}</Typography>
                  </TableCell>
                  <TableCell sx={{ maxWidth: 360 }}>
                    <Typography variant="body2">{row.Description}</Typography>
                  </TableCell>
                  <TableCell>
                    {Array.isArray(row.Steps)
                      ? `${row.Steps.length} step(s)`
                      : "-"}
                  </TableCell>
                </TableRow>
                <TableRow key={`${globalIndex}-details`}>
                  <TableCell colSpan={5} sx={{ pb: 0, pt: 0 }}>
                    <Collapse
                      in={!!expanded[globalIndex]}
                      timeout="auto"
                      unmountOnExit
                    >
                      <Box sx={{ margin: 1 }}>
                        {Array.isArray(row.Steps) && row.Steps.length > 0 ? (
                          <List dense>
                            {row.Steps.map((s, idx) => (
                              <ListItem key={idx} alignItems="flex-start">
                                <ListItemText
                                  primary={`Step ${
                                    s["Step Number"] || idx + 1
                                  }: ${s.Action}`}
                                  secondary={
                                    <>
                                      <Typography
                                        component="span"
                                        variant="body2"
                                      >
                                        Data: {JSON.stringify(s.Data)}
                                      </Typography>
                                      <br />
                                      <Typography
                                        component="span"
                                        variant="body2"
                                      >
                                        Expected: {s["Expected Result"]}
                                      </Typography>
                                    </>
                                  }
                                />
                              </ListItem>
                            ))}
                          </List>
                        ) : (
                          <Typography variant="body2">
                            No steps available
                          </Typography>
                        )}
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </>
            );
          })}
        </TableBody>
      </Table>
      <TablePagination
        component="div"
        count={rows ? rows.length : 0}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        rowsPerPageOptions={[]}
      />
      <Box sx={{ display: "flex", gap: 2, alignItems: "center", mt: 2 }}>
        {selectedCount > 0 && (
          <Typography variant="body2" sx={{ fontWeight: "bold", color: "#1976d2" }}>
            {selectedCount} of {rows.length} test case(s) selected
          </Typography>
        )}
      </Box>
      <Box sx={{ mt: 2 }}>
        <Button
          size="small"
          variant="contained"
          color="primary"
          sx={{ mr: 1 }}
          disabled={rows.length === 0 ? true : false}
          onClick={downloadHandler}
        >
          Download Excel
        </Button>
        <Button
          size="small"
          disabled={rows.length === 0 ? true : false}
          variant="contained"
          color="success"
          sx={{ mr: 1 }}
          loading={uploading}
          loadingPosition="end"
          onClick={uploadTestScriptsToJiraHandler}
          title={selectedCount > 0 ? `Upload ${selectedCount} selected test case(s)` : "Upload all test cases"}
        >
          {selectedCount > 0 ? `Upload Selected (${selectedCount})` : "Upload All to Jira"}
        </Button>
      </Box>
    </Paper>
  );
};

const OptimizedTestCaseTable = withTestCaseTable(TestCaseTable);
export default OptimizedTestCaseTable;
