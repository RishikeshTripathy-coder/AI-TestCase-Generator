const VALID_ENGLISH_WORDS = new Set([
  "this",
  "is",
  "a",
  "valid",
  "project",
  "requirement",
  "complete",
  "finish",
  "task",
  "document",
  "user",
  "email",
  "data",
  "analysis",
  "code",
  "design",
  "plan",
  "test",
  "review",
  "create",
  "update",
  "implement",
  "run",
  "execute",
  "process",
  "system",
  "shall",
  "provide",
  "information",
  "on",
  "the",
  "help",
  "page",
  "if",
  "you",
  "are",
  "facing",
  "an",
  "issue",
  "please",
  "contact",
  "or",
  "so",
  "that",
  "can",
  "get",
  "assistance",
  "when",
  "have",
  "questions",
  "and",
  "needs",
  "access",
  "for",
  "business",
  "purposes",
  "feature",
  "relates",
  "to",
  "local",
  "onboarding",
  "of",
  "affiliate",
  "approved",
  "core",
  "story",
  "as",
  "per",
  "system",
  "security",
  "admin",
  "sop",
]);

export const isValidRequirement = (req) => {
  // !req || req.trim().split(/\s+/).length
  if (!req || req.trim().length < 120) {
    return {
      value: false,
      message: "Requirement should contain at least 120 characters.",
    }; // Returns false if the string is empty or has fewer than 3 words
  }

  if (!/[a-zA-Z]/.test(req)) {
    return {
      value: false,
      message: "Invalid characters should in requirements.",
    }; // Returns false if no alphabetic characters are found
  }

  // Split the input string, process and filter the words
  const words = req
    .split(/\s+/) // Split string by one or more spaces
    .map((w) => w.toLowerCase()) // Convert each word to lowercase
    .filter((w) => /^[a-zA-Z]+$/.test(w) && !w.includes("@")); // Keep only valid words (no special chars or '@')

  // Find the words that are in the ENGLISH_WORDS set
  const engLike = words.filter((w) => VALID_ENGLISH_WORDS.has(w));
  console.log(engLike);

  // Calculate the ratio of English-like words to total words
  const ratio = words.length > 0 ? engLike.length / words.length : 0;

  // Return true if at least 30% of the words are English-like
  return {
    value: ratio >= 0.3,
    message:
      ratio >= 0.3
        ? ""
        : "Requirement should contain at least 30% valid English-like words.",
  };
};
