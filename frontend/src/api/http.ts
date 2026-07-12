import axios, {
  AxiosError,
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import { ElMessage } from "element-plus";

import type { ApiErrorDetail, ApiResponse, HttpRequestMeta } from "./types";

interface RequestConfigWithMeta extends InternalAxiosRequestConfig {
  meta?: HttpRequestMeta;
}

const apiBaseURL =
  import.meta.env.DEV && !import.meta.env.VITE_API_BASE_URL?.startsWith("http")
    ? "/api"
    : (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1");

export const http: AxiosInstance = axios.create({
  baseURL: apiBaseURL,
  timeout: 20_000,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const nextConfig = config as RequestConfigWithMeta;
  nextConfig.meta = {
    requestId: crypto.randomUUID(),
    startedAt: performance.now(),
  };
  return nextConfig;
});

http.interceptors.response.use(
  <T>(response: AxiosResponse<ApiResponse<T>>) => {
    if (!response.data.success) {
      const apiError = response.data.error;
      throw createApiError(apiError, response.status);
    }
    return response;
  },
  (error: AxiosError<ApiResponse<unknown>>) => {
    const message = resolveAxiosErrorMessage(error);
    ElMessage.error(message);
    return Promise.reject(error);
  },
);

export async function getApiData<T>(
  url: string,
  params?: Record<string, unknown>,
): Promise<T> {
  const response = await http.get<ApiResponse<T>>(url, { params });

  if (response.data.data === null) {
    throw createApiError(
      {
        code: "EMPTY_RESPONSE",
        message: "接口返回数据为空",
        details: { url },
      },
      response.status,
    );
  }

  return response.data.data;
}

function createApiError(
  error: ApiErrorDetail | null,
  statusCode: number,
): Error {
  const message =
    error?.message ?? `HTTP request failed with status ${statusCode}`;
  const nextError = new Error(message);
  nextError.name = error?.code ?? "API_ERROR";
  return nextError;
}

function resolveAxiosErrorMessage(
  error: AxiosError<ApiResponse<unknown>>,
): string {
  if (error.response?.data?.error?.message) {
    return error.response.data.error.message;
  }

  if (error.code === "ECONNABORTED") {
    return "请求超时，请稍后重试";
  }

  if (!error.response) {
    return "无法连接后端服务，请确认 API 已启动";
  }

  return `请求失败，状态码：${error.response.status}`;
}
