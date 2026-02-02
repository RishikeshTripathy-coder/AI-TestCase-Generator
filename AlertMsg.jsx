import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import { useEffect, useState } from "react";

// Snackbar onClose receives (event, reason). When reason === 'clickaway',
// we ignore it so the alert stays visible until the user explicitly closes it.
// This component also computes a small vertical offset so multiple Snackbars
// rendered across the app stack vertically instead of perfectly overlapping.
export default function AlertMsg({ msg, open, setOpen, severity = "success" }) {
  const [offset, setOffset] = useState(0);

  const handleClose = (event, reason) => {
    if (reason === "clickaway") {
      // ignore clickaway to keep the alert open until user explicitly closes it
      return;
    }
    setOpen(false);
  };

  useEffect(() => {
    // When this alert opens, compute how many snackbars are currently present
    // and assign an offset so they appear stacked. We use the .MuiSnackbar-root
    // class which MUI applies to the root container of Snackbars.
    if (open && typeof document !== "undefined") {
      const roots = document.querySelectorAll(".MuiSnackbar-root");
      // Subtract 1 because this Snackbar is likely already in the DOM by the time
      // this effect runs; we want earlier snackbars to be above this one.
      const index = Math.max(0, roots.length - 1);
      const gap = 72; // px gap between stacked snackbars
      setOffset(index * gap);
    }
  }, [open]);

  return (
    <>
      {/* Do not set autoHideDuration so the Snackbar stays until explicitly closed */}
      <Snackbar
        open={open}
        onClose={handleClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        // apply a margin-bottom based on computed offset so snackbars stack
        sx={{ mb: `${offset}px` }}
      >
        <Alert severity={severity} onClose={handleClose} sx={{ width: "100%" }}>
          {msg}
        </Alert>
      </Snackbar>
    </>
  );
}
