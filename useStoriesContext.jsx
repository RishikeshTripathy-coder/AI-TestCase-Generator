import { useContext } from "react";
import StoriesContext from "../context/storiesContext";

export const useStoriesContext = () => {
  return useContext(StoriesContext);
};
