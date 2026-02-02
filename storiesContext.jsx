import { createContext, useState } from "react";

const StoriesContext = createContext(null);

export const StoriesContextProvider = ({ children }) => {
  const [userStories, setUserStories] = useState([]);
  const [selectedStory, setSelectedStory] = useState({});
  const [testScripts, setTestScripts] = useState([]);
  const [fileContext, setFileContext] = useState(null);
  const [isTestScriptGenerating, setIsTestScriptGenerating] = useState(false);
  const values = {
    userStories,
    setUserStories,
    selectedStory,
    setSelectedStory,
    fileContext,
    setFileContext,
    testScripts,
    setTestScripts,
    isTestScriptGenerating,
    setIsTestScriptGenerating,
  };
  return (
    <StoriesContext.Provider value={values}>{children}</StoriesContext.Provider>
  );
};
export default StoriesContext;
