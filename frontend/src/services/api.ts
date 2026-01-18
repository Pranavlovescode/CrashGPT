const API_BASE_URL = "http://localhost:8000";

export interface QueryResponse {
  query: string;
  answer: string;
  sources: Array<{
    content: string;
    score: number;
    source: string;
  }>;
  collection_name: string;
}

export interface UploadResponse {
  filename: string;
  collection_name: string;
  status: string;
  message: string;
}

export async function uploadLog(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("collection_name", "mysql_crash_analysis");

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  console.log(response.body);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

export async function queryLogs(
  query: string,
  collectionName: string,
  limit: number = 6,
): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      collection_name: collectionName,
      limit,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Query failed");
  }

  return response.json();
}

export async function listCollections() {
  const response = await fetch(`${API_BASE_URL}/collections`);

  if (!response.ok) {
    throw new Error("Failed to list collections");
  }

  return response.json();
}

export async function getCollectionInfo(collectionName: string) {
  const response = await fetch(`${API_BASE_URL}/collections/${collectionName}`);

  if (!response.ok) {
    throw new Error("Failed to get collection info");
  }

  return response.json();
}
