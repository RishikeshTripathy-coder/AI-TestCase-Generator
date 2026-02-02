import { Box, Button, Container, Grid, Typography } from "@mui/material";
import HeroSection from "../HeroSection";
import JiraSetup from "../JiraSetup";
import RequirementDetails from "../RequirementDetails";
import ContextSetup from "../ContextSetup";
import UploadTestCases from "../UploadTestCases";
import TestCaseTable from "../TestCaseTable";
import { useState, useRef, useCallback } from "react";
import SelectionType from "../selection-type/SelectionType";
import ManualGeneration from "../manual-generation/ManualGeneration";
import { StoriesContextProvider } from "../../context/storiesContext";
import GenerateButton from "../button/GenerateButton";

const Home = () => {
  console.count("-> Home");
  const [selectedContext, setSelectedContext] = useState("No Context");
  const [value, setValue] = useState("automate");

  // Ref to get the input requirement from ContextSetup when selectedContext is "Manual Input"
  // const contextSetupRef = useRef(null);

  // Ref to get the manual input from ManualGeneration Component
  const manualInputRef = useRef(null);

  // Ref to store the scraped URL text
  const scrapeUrlTextRef = useRef(null);

  const handleChange = useCallback((event) => {
    console.log("SelectionType changed to:", event.target.value);
    setValue(event.target.value);
  }, []);

  const handleSelectContext = useCallback((event) => {
    setSelectedContext(event.target.value);
  }, []);
  return (
    <>
      <HeroSection />
      <Container maxWidth="lg">
        <StoriesContextProvider>
          <SelectionType value={value} handleChange={handleChange} />
          {value === "automate" && (
            <>
              <JiraSetup />
              <RequirementDetails />
            </>
          )}
          {value === "manual" && <ManualGeneration ref={manualInputRef} />}

          <Box className="context_upload_test_case_container">
            <Grid container spacing={2} p={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <ContextSetup
                  ref={scrapeUrlTextRef}
                  selectedContext={selectedContext}
                  handleSelectContext={handleSelectContext}
                />
              </Grid>
              <Grid height={"auto"} size={{ xs: 12, md: 6 }}>
                <UploadTestCases selectedContext={selectedContext} />
              </Grid>
              <GenerateButton
                // contextSetupRef={contextSetupRef}
                generationType={value}
                manualInputRef={manualInputRef}
                scrapeUrlTextRef={scrapeUrlTextRef}
              />
            </Grid>
          </Box>
          <TestCaseTable />
        </StoriesContextProvider>
      </Container>
    </>
  );
};

export default Home;
