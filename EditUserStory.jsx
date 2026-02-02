import * as React from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Modal from "@mui/material/Modal";
import UserStory from "../user-story/UserStory";

const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: "80%",
  bgcolor: "background.paper",
  boxShadow: 24,
  borderRadius: 1,
  p: 2,
};

export default function EditUserStory({ onEditToggle }) {
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => {
    setOpen(true);
    if (typeof onEditToggle === "function") onEditToggle();
  };
  const handleClose = () => setOpen(false);

  return (
    <div>
      <Button variant="contained" size="small" onClick={handleOpen}>
        Edit
      </Button>
      <Modal
        open={open}
        onClose={(event, reason) => {
          if (reason === "backdropClick") {
            return; // Prevent close
          }
          handleClose(); // Only close for other reasons (e.g., Escape key)
        }}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={style}>
          <Typography id="modal-modal-title" variant="h6" component="h2">
            Edit User Story - User Story 1
          </Typography>
          <Typography
            component={"span"}
            id="modal-modal-description"
            sx={{ mt: 2 }}
          >
            <UserStory type="edit" handleClose={handleClose} />
          </Typography>
        </Box>
      </Modal>
    </div>
  );
}
