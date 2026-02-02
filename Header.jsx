import { Typography } from "@mui/material";
import Navbar from "../navbar/Navbar";
import { Link } from "react-router-dom";

const Header = () => {
  console.count("Header");
  return (
    <>
      <header>
        <Typography
          variant={"h4"}
          sx={{ color: "primary" }}
          fontWeight={"bold"}
          textAlign={"left"}
        >
          <Link to={"/"} style={{ textDecoration: "none" }}>
           Test Case Generator
          </Link>
        </Typography>
        <Navbar />
      </header>
    </>
  );
};

export default Header;
