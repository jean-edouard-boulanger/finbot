const GENERIC_FALLBACK = "Something went wrong. Please try again.";

const RUNTIME_GENERIC_MESSAGES = new Set([
  "Response returned an error code",
  "The request failed and the interceptors did not return an alternative response",
]);

export function formatApiError(error: unknown): string {
  if (error instanceof Error) {
    const message = error.message?.trim();
    if (message && !RUNTIME_GENERIC_MESSAGES.has(message)) {
      return message;
    }
  }
  if (typeof error === "string" && error.trim().length > 0) {
    return error;
  }
  return GENERIC_FALLBACK;
}
