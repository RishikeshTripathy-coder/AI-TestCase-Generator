def extract_text_from_adf(adf: dict) -> str:
    """
    Extract plain text from Jira's ADF (Atlassian Document Format).
    Preserves bullets and indentation, but avoids numbered prefixes.
    """

    if not adf or not isinstance(adf, dict):
        return ""

    lines = []

    def walk(nodes, indent=""):
        if not nodes:
            return

        for node in nodes:
            node_type = node.get("type")
            content = node.get("content", [])

            if node_type == "text":
                lines.append(indent + node.get("text", ""))

            elif node_type == "paragraph":
                walk(content, indent)
                lines.append("")  # newline between paragraphs

            elif node_type in ("bulletList", "orderedList"):
                for item in content:
                    # For both bulletList and orderedList, just use dash (-)
                    walk(item.get("content", []), indent + "- ")

            elif node_type == "listItem":
                walk(content, indent)

            else:
                walk(content, indent)

    walk(adf.get("content", []))

    # Clean up trailing empty lines
    return "\n".join([line for line in lines if line.strip()]).strip()


# print(extract_text_from_adf({
#   "type": "doc",
#   "version": 1,
#   "content": [
#     {
#       "type": "paragraph",
#       "content": [
#         {"type": "text", "text": "As a user, I want to log in securely."}
#       ]
#     },
#     {
#       "type": "bulletList",
#       "content": [
#         {
#           "type": "listItem",
#           "content": [
#             {
#               "type": "paragraph",
#               "content": [
#                 {"type": "text", "text": "Use email and password"}
#               ]
#             }
#           ]
#         },
#         {
#           "type": "listItem",
#           "content": [
#             {
#               "type": "paragraph",
#               "content": [
#                 {"type": "text", "text": "Validate with OTP"}
#               ]
#             }
#           ]
#         }
#       ]
#     }
#   ]
# }
# ))