import { Button } from "@mui/material";
import { useLocation } from "react-router-dom";

const Navbar = () => {
  const location = useLocation();

  const handleSampleTemplatesClick = () => {
    // Open the context-template page in New TAB
    window.open("/context-template");
  };

  const handleUserGuideClick = () => {
    // Open the user manual PDF in new tab (you can change this if needed)
    window.open("/AI Use Case Test Case Generator.pdf", "_blank");
  };

  return (
    <nav>
      <ul style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <li>
          <Button
            color="inherit"
            sx={{ fontWeight: "bold", textDecoration: "underline" }}
            onClick={handleSampleTemplatesClick}
            disabled={location.pathname === "/context-template"}
          >
            Sample Context Templates
          </Button>
        </li>
        <li>
          <Button
            color="inherit"
            sx={{ fontWeight: "bold", textDecoration: "underline" }}
            onClick={handleUserGuideClick}
          >
            User Manual
          </Button>
        </li>
      </ul>
    </nav>
  );
};

export default Navbar;
