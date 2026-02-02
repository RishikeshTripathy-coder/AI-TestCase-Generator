export const mapContextToType = (label) => {
  switch (label) {
    case "Upload JSON":
      return "json";
    case "Upload YAML":
      return "yaml";
    case "Upload Plain Text":
      return "text";
    case "Upload BRD":
      return "brd";
    // case "Upload PDF/DOCX":
    //   return "pdf"; // or "docx" if needed
    case "Scrape URL":
      return "url";
    case "Manual Input":
      return "manual";
    case "Upload Existing Test Case":
      return "test_case";
    default:
      return "none";
  }
};
