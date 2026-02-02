export const TEMPLATE_DATA = [
  {
    id: "json",
    title: "JSON",
    icon: "🧩",
    content: `{
  "appName": "SmartBank",
  "overview": "Mobile banking app for managing accounts, transfers, and bill payments.",
  "uiScreens": [
    {
      "screenName": "Login Screen",
      "description": "User login via credentials or biometrics.",
      "keyElements": ["Username field", "Password field", "Login button"],
      "navigation": "First screen; leads to Dashboard on success."
    }
  ],
  "functionality": [
    {
      "featureName": "Fund Transfer",
      "description": "Transfer money between accounts.",
      "relatedScreens": ["Dashboard", "Transfer Screen"],
      "businessRules": ["OTP required for transfers > $10,000"]
    }
  ],
  "userRoles": [
    {
      "roleName": "Standard User",
      "permissions": ["View accounts", "Transfer funds"],
      "featureAccess": ["Login Screen", "Dashboard", "Transfer"]
    }
  ],
  "edgeCasesAndConstraints": [
    "Login fails after 5 incorrect attempts"
  ],
  "testDataGuidelines": [
    "Use usernames like user001",
    "Test transfer amounts: $0, $10,000, $10,001"
  ],
  "additionalNotes": "Biometric login supported only on compatible devices."
}`,
  },
  {
    id: "yaml",
    title: "YAML",
    icon: "📜",
    content: `appName: SmartBank
overview: Mobile banking app for managing accounts, transfers, and bill payments.
uiScreens:
  - screenName: Login Screen
    description: User login via credentials or biometrics.
    keyElements: [Username field, Password field, Login button]
    navigation: First screen; leads to Dashboard on success.
functionality:
  - featureName: Fund Transfer
    description: Transfer money between accounts.
    relatedScreens: [Dashboard, Transfer Screen]
    businessRules: [OTP required for transfers > $10,000]
userRoles:
  - roleName: Standard User
    permissions: [View accounts, Transfer funds]
    featureAccess: [Login Screen, Dashboard, Transfer]
edgeCasesAndConstraints:
  - Login fails after 5 incorrect attempts
testDataGuidelines:
  - Use usernames like user001
  - Test transfer amounts: $0, $10,000, $10,001
additionalNotes: Biometric login supported only on compatible devices.`,
  },
  {
    id: "plainText",
    title: "Plain Text",
    icon: "📝",
    content: `• App Name: SmartBank
• Overview: Mobile banking app for managing accounts, transfers, and bill payments
• UI Screens:
  o Login Screen
    ▪ Description: User login via credentials or biometrics
    ▪ Key Elements: Username field, Password field, Login button
    ▪ Navigation: Leads to Dashboard on success
• Functionality:
  o Fund Transfer
    ▪ Description: Transfer money between accounts
    ▪ Related Screens: Dashboard, Transfer Screen
    ▪ Business Rules: OTP required for transfers > $10,000
• User Roles:
  o Standard User
    ▪ Permissions: View accounts, Transfer funds
    ▪ Feature Access: Login Screen, Dashboard, Transfer
• Edge Cases & Constraints: Login fails after 5 incorrect attempts
• Test Data Guidelines: Use usernames like user001; Test transfer amounts: $0, $10,000, $10,001
• Additional Notes: Biometric login supported only on compatible devices`,
  },
];
