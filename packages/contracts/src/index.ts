export type Confidence = "confirmed" | "needs_review";

export interface Evidence {
  quote: string;
  location?: string;
  confidence: Confidence;
}

export interface PolicyAnalysis {
  serviceName: string;
  policyUrl: string;
  collectedData: string[];
  purposes: string[];
  retentionPeriods: string[];
  thirdPartySharing: boolean | null;
  outsourcing: string[];
  userRights: string[];
  evidence: Evidence[];
  analysisDate: string;
}

export interface ServiceRecord {
  id: string;
  serviceName: string;
  domain: string;
  recordedAt: string;
  dataTypes: string[];
  optionalConsent: "accepted" | "rejected" | "not_applicable";
  source: "detected" | "user_confirmed" | "policy_stated";
  policy?: PolicyAnalysis;
}
