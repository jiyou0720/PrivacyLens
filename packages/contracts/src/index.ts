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

export type DetectionStatus = "confirmed" | "inferred" | "needs_review";
export type Requirement = "required" | "optional" | "unknown";

export type PersonalDataCategory =
  | "name"
  | "email"
  | "phone"
  | "address"
  | "birth_date"
  | "gender"
  | "nickname"
  | "location"
  | "payment"
  | "identifier"
  | "password"
  | "unknown";

export type ConsentCategory =
  | "privacy_collection"
  | "third_party_sharing"
  | "marketing"
  | "location"
  | "terms"
  | "all"
  | "unknown";

export interface ElementEvidence {
  label?: string;
  attributes: {
    tagName: "input" | "select" | "textarea";
    type?: string;
    name?: string;
    id?: string;
    autocomplete?: string;
    placeholder?: string;
    required?: boolean;
    ariaRequired?: boolean;
  };
  nearbyText?: string;
}

export interface DetectedField {
  id: string;
  category: PersonalDataCategory;
  requirement: Requirement;
  status: DetectionStatus;
  evidence: ElementEvidence;
}

export interface ConsentItem {
  id: string;
  category: ConsentCategory;
  title: string;
  requirement: Requirement;
  checkedByDefault: boolean;
  disabled: boolean;
  status: DetectionStatus;
  documentUrl?: string;
}

export interface DetectionWarning {
  ruleId: "preselected-optional-consent";
  severity: "warning";
  message: string;
  evidenceIds: string[];
}

export interface PageScanResult {
  schemaVersion: "1.0";
  requestId: string;
  scannedAt: string;
  page: {
    domain: string;
    url: string;
    title: string;
  };
  fields: DetectedField[];
  consents: ConsentItem[];
  warnings: DetectionWarning[];
  privacy: {
    inputValuesCollected: false;
    fullHtmlCollected: false;
  };
}

export type ScanErrorCode =
  | "NO_ACTIVE_TAB"
  | "UNSUPPORTED_PAGE"
  | "INJECTION_FAILED"
  | "UNKNOWN_ERROR";

export interface ScanError {
  code: ScanErrorCode;
  message: string;
}

export type ExtensionMessage =
  | { type: "SCAN_PAGE"; requestId: string }
  | { type: "PAGE_SCAN_STARTED"; requestId: string }
  | { type: "PAGE_SCAN_COMPLETED"; requestId: string; payload: PageScanResult }
  | { type: "PAGE_SCAN_FAILED"; requestId: string; error: ScanError };
