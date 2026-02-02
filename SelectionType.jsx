import Radio from "@mui/material/Radio";
import RadioGroup from "@mui/material/RadioGroup";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormControl from "@mui/material/FormControl";
import FormLabel from "@mui/material/FormLabel";
import { memo } from "react";
import { useStoriesContext } from "../../hooks/useStoriesContext";

// SelectionType HOC
const withSelectionType = (Component) => {
  const MemoizedComponent = memo(Component);
  return (props) => {
    const { isTestScriptGenerating } = useStoriesContext();
    return (
      <MemoizedComponent
        {...props}
        isTestScriptGenerating={isTestScriptGenerating}
      />
    );
  };
};

function SelectionType({ value, handleChange, isTestScriptGenerating }) {
  console.count("SelectionType");
  return (
    <FormControl>
      <FormLabel
        id="demo-row-radio-buttons-group-label"
        sx={{ fontWeight: "bold" }}
      >
        Test Case Generation Type
      </FormLabel>
      <RadioGroup
        row
        aria-labelledby="demo-row-radio-buttons-group-label"
        name="row-radio-buttons-group"
        value={value}
        onChange={handleChange}
      >
        <FormControlLabel
          disabled={isTestScriptGenerating}
          value="automate"
          control={<Radio />}
          label="JIRA"
        />
        <FormControlLabel
          disabled={isTestScriptGenerating}
          value="manual"
          control={<Radio />}
          label="Manual"
        />
      </RadioGroup>
    </FormControl>
  );
}

const OptimizedSelectionType = withSelectionType(SelectionType);

export default OptimizedSelectionType;
