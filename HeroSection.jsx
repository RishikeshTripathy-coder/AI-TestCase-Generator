import { Box, Typography, Button } from "@mui/material";
import { memo } from "react";

function HeroSection() {
  console.count("HeroSection");
  return (
    <Box
      sx={{
        // background: "linear-gradient(135deg, #d8d8ff93, transparent)",
        padding: 3,
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
      }}
    >
      <Typography variant="h4" gutterBottom>
        🤖ITQS_AI_Powered Test Case Generator
      </Typography>
      <Typography
        variant="h6"
        width={"53%"}
        margin={"0 auto"}
        color="textSecondary"
        fontSize={"1.2rem"}
      >
        Transform your{" "}
        <Typography
          component={"span"}
          sx={{ color: "rebeccapurple", fontWeight: "bold" }}
        >
          User Stories
        </Typography>{" "}
        into executable Jira{" "}
        <Typography
          component={"span"}
          sx={{ color: "rebeccapurple", fontWeight: "bold" }}
        >
          Test Scripts
        </Typography>{" "}
        with ease. Enter your Jira API key to fetch user stories and generate
        structured test cases.
      </Typography>
      {/* <Button variant="contained" color="primary">
        Get Started
      </Button> */}
    </Box>
  );
}

export default memo(HeroSection);
