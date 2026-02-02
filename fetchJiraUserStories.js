import config from "../config";

export const fetchJiraUserStories = async (jiraAPIKey, jqlQuery) => {
  try {
    const resp = await fetch(`${config.fetchUrl}/jira/stories`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ jira_api_key: jiraAPIKey, jql: jqlQuery }),
    });
    const data = await resp.json();
    if (resp.ok) {
      return data;
    } else {
      throw new Error(data);
    }
  } catch (error) {
    console.error(error.message);
  }
};
