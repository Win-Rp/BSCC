const posthogProjectKey = import.meta.env.VITE_POSTHOG_KEY?.trim();
const posthogHost = import.meta.env.VITE_POSTHOG_HOST?.trim() || "https://us.i.posthog.com";

/**
 * Starts product analytics only for the public web application when a project
 * key is supplied at build time. The extension build and local builds without
 * a key never contact PostHog.
 */
export async function initializeAnalytics() {
  if (!posthogProjectKey || typeof window === "undefined") {
    return;
  }

  const { default: posthog } = await import("posthog-js");
  posthog.init(posthogProjectKey, {
    api_host: posthogHost,
    defaults: "2026-05-30",
    capture_pageview: "history_change",
    autocapture: false,
    disable_session_recording: true,
    person_profiles: "identified_only"
  });
}
