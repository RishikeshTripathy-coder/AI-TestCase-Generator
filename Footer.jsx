import { Typography } from "@mui/material";

const Footer = () => {
  return (
    <>
      <footer className="footer">
        <Typography
          component={"h6"}
          textAlign={"center"}
          p={2}
          fontWeight={"bold"}
        >
          &copy;AI Powered Test Case Generator<br />    
        </Typography>
      </footer>
    </>
  );
};

export default Footer;
